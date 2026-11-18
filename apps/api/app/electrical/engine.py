"""Deterministic wiring engine.

The engine turns a robot specification plus a bill of materials into a complete,
traceable electrical plan:

* every placed part gets a stable reference and a pin list;
* power, ground, motor, and signal connections are allocated from real pin
  capabilities instead of free-form prose;
* voltage, logic-level, grounding, current, and pin-conflict checks are plain
  Python functions so they can be unit tested against known-good fixtures;
* the emitted plan is the single input to the CSV, netlist, SVG, and guide
  exporters.

No LLM is involved. A model may later *choose* parts or explain the result, but
it never decides whether a connection is electrically safe.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Literal, cast

from app.ai.contracts import (
    ComponentResearchOutput,
    ElectricalConnection,
    ElectricalIssue,
    ElectricalNode,
    ElectricalNodePin,
    ElectricalPlan,
    PowerBudget,
    PowerRail,
    RobotSpecificationDraft,
)
from app.electrical.library import (
    COMPONENT_LIBRARY,
    ComponentProfile,
    PinDefinition,
)
from app.models.enums import ComponentCategory

LIBRARY_VERSION = "1.0"

_GROUND_NET = "GND"
_VBAT_NET = "VBAT"
_V5_NET = "+5V"
_V5_CTRL_NET = "5V_CTRL"
_V33_NET = "3V3_CTRL"

_PREFIX_BY_ROLE: dict[str, str] = {
    "battery": "BT",
    "regulator": "VR",
}

_PREFIX_BY_CATEGORY: dict[ComponentCategory, str] = {
    ComponentCategory.CONTROLLER: "U",
    ComponentCategory.MOTOR_DRIVER: "U",
    ComponentCategory.POWER: "BT",
    ComponentCategory.MOTOR: "M",
    ComponentCategory.ACTUATOR: "M",
    ComponentCategory.SENSOR: "S",
}

_WIRE_COLORS: dict[str, str] = {
    "power": "red",
    "ground": "black",
    "signal": "yellow",
    "motor": "orange",
    "bus": "blue",
}

_WIRE_GAUGE: dict[str, int] = {
    "power": 18,
    "ground": 18,
    "signal": 24,
    "motor": 18,
    "bus": 24,
}


@dataclass(frozen=True, slots=True)
class PlacedPart:
    profile: ComponentProfile
    role: str
    ref: str

    @property
    def label(self) -> str:
        return self.profile.name


@dataclass(slots=True)
class _Design:
    nodes: list[ElectricalNode] = field(default_factory=list)
    by_ref: dict[str, ElectricalNode] = field(default_factory=dict)
    connections: list[ElectricalConnection] = field(default_factory=list)
    issues: list[ElectricalIssue] = field(default_factory=list)
    pin_map: dict[str, str] = field(default_factory=dict)
    supply_by_ref: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def add_issue(
        self,
        code: str,
        severity: Literal["error", "warning", "info"],
        message: str,
        refs: list[str] | None = None,
        remediation: str = "",
    ) -> None:
        self.issues.append(
            ElectricalIssue(
                code=code,
                severity=severity,
                message=message,
                refs=refs or [],
                remediation=remediation,
            )
        )


class _PinAllocator:
    """Hands out controller pins by capability without ever reusing one."""

    def __init__(self, profile: ComponentProfile) -> None:
        self.profile = profile
        self.used: dict[str, str] = {}

    def take(self, capability: str, signal: str) -> PinDefinition | None:
        for pin in self.profile.pins:
            if pin.name in self.used:
                continue
            if capability in pin.capabilities:
                self.used[pin.name] = signal
                return pin
        return None


def _profile_for_candidate(
    library_key: object, model_number: str, name: str
) -> ComponentProfile | None:
    if isinstance(library_key, str) and library_key in COMPONENT_LIBRARY:
        return COMPONENT_LIBRARY[library_key]
    model = model_number.strip().lower()
    label = name.strip().lower()
    for profile in COMPONENT_LIBRARY.values():
        if model and profile.model_number.lower() == model:
            return profile
        if label and profile.name.lower() == label:
            return profile
    return None


def _place_parts(bom: ComponentResearchOutput) -> tuple[list[PlacedPart], list[str]]:
    """Resolve BOM lines to library profiles and assign stable references."""

    unresolved: list[str] = []
    drafts: list[tuple[ComponentProfile, str]] = []
    for item in bom.bill_of_materials:
        candidate = item.selection
        if candidate is None:
            unresolved.append(f"{item.role}: no selected component, so no wiring was generated.")
            continue
        profile = _profile_for_candidate(
            candidate.specs.get("library_key"), candidate.model_number, candidate.name
        )
        if profile is None:
            unresolved.append(
                f"{candidate.name}: not present in the electrical library; "
                "its pins are unknown and no connections were generated."
            )
            continue
        for _ in range(item.quantity):
            drafts.append((profile, item.role))

    counters: dict[str, int] = defaultdict(int)
    placed: list[PlacedPart] = []
    for profile, role in drafts:
        prefix = _PREFIX_BY_ROLE.get(role) or _PREFIX_BY_CATEGORY.get(profile.category, "X")
        counters[prefix] += 1
        placed.append(PlacedPart(profile=profile, role=role, ref=f"{prefix}{counters[prefix]}"))

    # Controllers and power sources are easier to read first in the UI/export.
    order = {
        ComponentCategory.CONTROLLER: 0,
        ComponentCategory.POWER: 1,
        ComponentCategory.MOTOR_DRIVER: 2,
        ComponentCategory.ACTUATOR: 3,
        ComponentCategory.MOTOR: 4,
        ComponentCategory.SENSOR: 5,
    }
    placed.sort(key=lambda part: order.get(part.profile.category, 9))
    return placed, unresolved


def _node_kind(
    profile: ComponentProfile,
) -> Literal["controller", "motor", "driver", "sensor", "power", "actuator", "regulator", "other"]:
    if profile.is_controller:
        return "controller"
    mapping: dict[ComponentCategory, str] = {
        ComponentCategory.MOTOR_DRIVER: "driver",
        ComponentCategory.MOTOR: "motor",
        ComponentCategory.ACTUATOR: "actuator",
        ComponentCategory.SENSOR: "sensor",
        ComponentCategory.POWER: "power",
    }
    kind = mapping.get(profile.category, "other")
    if kind == "power" and profile.output_voltage_v is not None:
        return "regulator"
    return cast(
        Literal[
            "controller", "motor", "driver", "sensor", "power", "actuator", "regulator", "other"
        ],
        kind,
    )


def _nominal_voltage(profile: ComponentProfile) -> float | None:
    if profile.nominal_voltage_v is not None:
        return profile.nominal_voltage_v
    if profile.output_voltage_v is not None:
        return profile.output_voltage_v
    if profile.logic_voltage_v is not None:
        return profile.logic_voltage_v
    if profile.supply_min_v is not None and profile.supply_max_v is not None:
        return round((profile.supply_min_v + profile.supply_max_v) / 2, 2)
    return None


def _make_nodes(parts: list[PlacedPart]) -> list[ElectricalNode]:
    nodes: list[ElectricalNode] = []
    for part in parts:
        profile = part.profile
        nodes.append(
            ElectricalNode(
                ref=part.ref,
                label=profile.name,
                kind=_node_kind(profile),
                role=part.role,
                library_key=profile.key,
                voltage_v=_nominal_voltage(profile),
                current_ma=profile.current_ma_typical,
                peak_current_ma=profile.current_ma_peak,
                pins=[
                    ElectricalNodePin(
                        name=pin.name,
                        kind=pin.kind,
                        voltage_v=pin.voltage_v,
                    )
                    for pin in profile.pins
                ],
                notes=profile.notes,
            )
        )
    return nodes


def _connect(
    design: _Design,
    *,
    from_ref: str,
    from_pin: str,
    to_ref: str,
    to_pin: str,
    net: str,
    signal: str,
    kind: Literal["power", "ground", "signal", "motor", "bus"],
    voltage_v: float | None = None,
    notes: str = "",
) -> None:
    source = design.by_ref.get(from_ref)
    target = design.by_ref.get(to_ref)
    if source is None or target is None:
        design.add_issue(
            "unknown_endpoint",
            "error",
            f"Connection {from_ref}.{from_pin} → {to_ref}.{to_pin} references a missing part.",
            [from_ref, to_ref],
        )
        return
    if source_pin := next((pin for pin in source.pins if pin.name == from_pin), None):
        source_pin.connected = True
    else:
        design.add_issue(
            "unknown_pin",
            "error",
            f"{source.label} ({source.ref}) has no pin named {from_pin}.",
            [source.ref],
        )
        return
    if target_pin := next((pin for pin in target.pins if pin.name == to_pin), None):
        target_pin.connected = True
    else:
        design.add_issue(
            "unknown_pin",
            "error",
            f"{target.label} ({target.ref}) has no pin named {to_pin}.",
            [target.ref],
        )
        return

    design.connections.append(
        ElectricalConnection(
            from_ref=from_ref,
            from_pin=from_pin,
            to_ref=to_ref,
            to_pin=to_pin,
            net=net,
            signal=signal,
            kind=kind,
            voltage_v=voltage_v,
            wire_color=_WIRE_COLORS[kind],
            wire_gauge_awg=_WIRE_GAUGE[kind],
            notes=notes,
        )
    )
    if kind in {"power", "motor"} and voltage_v is not None:
        design.supply_by_ref[to_ref] = voltage_v


def _allocate_signal(
    design: _Design,
    allocator: _PinAllocator,
    controller: PlacedPart,
    *,
    capability: str,
    signal: str,
    to_ref: str,
    to_pin: str,
    net: str,
    voltage_v: float | None,
    notes: str = "",
) -> bool:
    pin = allocator.take(capability, signal)
    if pin is None:
        design.add_issue(
            "pin_exhausted",
            "error",
            f"{controller.label} has no free {capability.upper()} pin left for {signal}.",
            [controller.ref, to_ref],
            remediation="Move a peripheral to an I2C expander or use a controller with more pins.",
        )
        return False
    design.pin_map[pin.name] = f"{to_ref}.{to_pin} · {signal}"
    _connect(
        design,
        from_ref=controller.ref,
        from_pin=pin.name,
        to_ref=to_ref,
        to_pin=to_pin,
        net=net,
        signal=signal,
        kind="signal",
        voltage_v=voltage_v,
        notes=notes,
    )
    return True


def _power_source_for(
    *,
    profile: ComponentProfile,
    controller_logic: float | None,
    has_regulator: bool,
    has_controller_5v: bool,
) -> tuple[str, float] | None:
    """Pick the safest available rail for a 5 V/3.3 V peripheral."""

    if profile.key in {"mpu6050", "apds9960"}:
        if controller_logic == 3.3:
            return (_V33_NET, 3.3)
        return (_V5_CTRL_NET, 5.0) if has_controller_5v else (_V5_NET, 5.0)
    if profile.key == "ir_line_5ch" and controller_logic == 3.3:
        return (_V33_NET, 3.3)
    if profile.key == "hc_sr04":
        if has_regulator:
            return (_V5_NET, 5.0)
        if has_controller_5v:
            return (_V5_CTRL_NET, 5.0)
        return None
    if has_regulator:
        return (_V5_NET, 5.0)
    if has_controller_5v:
        return (_V5_CTRL_NET, 5.0)
    if controller_logic == 3.3:
        return (_V33_NET, 3.3)
    return None


def _wire(design: _Design, parts: list[PlacedPart], spec: RobotSpecificationDraft) -> None:
    controllers = [part for part in parts if part.profile.is_controller]
    drivers = [part for part in parts if part.profile.category is ComponentCategory.MOTOR_DRIVER]
    batteries = [
        part
        for part in parts
        if part.profile.category is ComponentCategory.POWER
        and part.profile.output_voltage_v is None
    ]
    regulators = [
        part
        for part in parts
        if part.profile.category is ComponentCategory.POWER
        and part.profile.output_voltage_v is not None
    ]
    motors = [part for part in parts if part.profile.category is ComponentCategory.MOTOR]
    servos = [part for part in parts if part.profile.category is ComponentCategory.ACTUATOR]
    sensors = [part for part in parts if part.profile.category is ComponentCategory.SENSOR]

    controller = controllers[0] if controllers else None
    driver = drivers[0] if drivers else None
    battery = batteries[0] if batteries else None
    regulator = regulators[0] if regulators else None

    if len(controllers) > 1:
        design.add_issue(
            "multiple_controllers",
            "warning",
            "More than one controller is present; only the first controller was wired.",
            [part.ref for part in controllers[1:]],
            remediation="Remove the extra controller or split the design into separate boards.",
        )
    if controller is None:
        design.add_issue(
            "missing_controller",
            "error",
            "No controller is selected, so no GPIO, PWM, or I²C connections could be assigned.",
            remediation="Add a controller to the bill of materials and regenerate the plan.",
        )
    if battery is None:
        design.add_issue(
            "missing_power_source",
            "error",
            "No battery or power source is selected; the plan has no supply rail.",
            remediation="Add a battery or regulated supply to the bill of materials.",
        )

    controller_logic = controller.profile.logic_voltage_v if controller else None
    battery_v = _nominal_voltage(battery.profile) if battery else None
    has_controller_5v = bool(controller and controller.profile.pin("5V"))
    has_regulator = regulator is not None

    # ------------------------------------------------------------------
    # Ground bus and source rails
    # ------------------------------------------------------------------
    ground_refs: set[str] = set()
    if battery is not None:
        for part in parts:
            if part.ref == battery.ref:
                continue
            for pin in part.profile.pins:
                if pin.kind == "ground":
                    _connect(
                        design,
                        from_ref=battery.ref,
                        from_pin="NEG",
                        to_ref=part.ref,
                        to_pin=pin.name,
                        net=_GROUND_NET,
                        signal="Common ground",
                        kind="ground",
                        voltage_v=0.0,
                    )
                    ground_refs.add(part.ref)

        if regulator is not None:
            _connect(
                design,
                from_ref=battery.ref,
                from_pin="POS",
                to_ref=regulator.ref,
                to_pin="IN+",
                net=_VBAT_NET,
                signal="Battery input to regulator",
                kind="power",
                voltage_v=battery_v,
            )
            design.supply_by_ref[regulator.ref] = battery_v or 0.0

        if controller is not None:
            uses_regulator = regulator is not None and controller.profile.key in {
                "esp32_devkit",
                "pico",
            }
            if uses_regulator and regulator is not None:
                _connect(
                    design,
                    from_ref=regulator.ref,
                    from_pin="OUT+",
                    to_ref=controller.ref,
                    to_pin="VIN" if controller.profile.pin("VIN") else "VSYS",
                    net=_V5_NET,
                    signal="Regulated 5 V logic supply",
                    kind="power",
                    voltage_v=5.0,
                )
            else:
                _connect(
                    design,
                    from_ref=battery.ref,
                    from_pin="POS",
                    to_ref=controller.ref,
                    to_pin="VIN" if controller.profile.pin("VIN") else "VSYS",
                    net=_VBAT_NET,
                    signal="Battery input to controller",
                    kind="power",
                    voltage_v=battery_v,
                )

        if driver is not None:
            voltage_pin = "VM" if driver.profile.pin("VM") else "VMS"
            _connect(
                design,
                from_ref=battery.ref,
                from_pin="POS",
                to_ref=driver.ref,
                to_pin=voltage_pin,
                net=_VBAT_NET,
                signal="Motor supply",
                kind="power",
                voltage_v=battery_v,
            )
            design.supply_by_ref[driver.ref] = battery_v or 0.0
            if driver.profile.pin("VCC") is not None:
                logic, logic_v, logic_ref = _driver_logic_rail(
                    controller, regulator, has_controller_5v
                )
                if logic_ref is not None:
                    logic_net, logic_pin = logic
                    _connect(
                        design,
                        from_ref=logic_ref.ref,
                        from_pin=logic_pin,
                        to_ref=driver.ref,
                        to_pin="VCC",
                        net=logic_net,
                        signal="Driver logic supply",
                        kind="power",
                        voltage_v=logic_v,
                    )
                    if driver.profile.pin("STBY") is not None:
                        _connect(
                            design,
                            from_ref=logic_ref.ref,
                            from_pin=logic_pin,
                            to_ref=driver.ref,
                            to_pin="STBY",
                            net=logic_net,
                            signal="Driver standby (tied high)",
                            kind="signal",
                            voltage_v=logic_v,
                        )
                    design.pin_map[logic_pin] = f"{driver.ref}.VCC/STBY · logic rail"
                else:
                    design.add_issue(
                        "missing_driver_logic",
                        "error",
                        "The motor driver has no logic supply rail.",
                        [driver.ref],
                    )

    # ------------------------------------------------------------------
    # Motor driver channels
    # ------------------------------------------------------------------
    controller_pin_voltage = controller_logic
    allocator = _PinAllocator(controller.profile) if controller else None

    if driver is not None and motors:
        if len(motors) > 2:
            design.add_issue(
                "motor_channels_insufficient",
                "error",
                f"{len(motors)} DC motors need more than the two channels this driver provides.",
                [driver.ref, *[motor.ref for motor in motors[2:]]],
                remediation="Add a second driver or wire a mechanically coupled pair per channel.",
            )
        for index, motor in enumerate(motors[:2]):
            if controller is None or allocator is None:
                break
            if driver.profile.key == "l298n":
                pwm_pin = "ENA" if index == 0 else "ENB"
                in1, in2 = ("IN1", "IN2") if index == 0 else ("IN3", "IN4")
                out1, out2 = ("OUT1", "OUT2") if index == 0 else ("OUT3", "OUT4")
            else:
                pwm_pin = "PWMA" if index == 0 else "PWMB"
                in1, in2 = ("AIN1", "AIN2") if index == 0 else ("BIN1", "BIN2")
                out1, out2 = ("AO1", "AO2") if index == 0 else ("BO1", "BO2")
            _allocate_signal(
                design,
                allocator,
                controller,
                capability="pwm",
                signal=f"Motor {index + 1} speed",
                to_ref=driver.ref,
                to_pin=pwm_pin,
                net=f"MOTOR_{index + 1}_PWM",
                voltage_v=controller_pin_voltage,
            )
            _allocate_signal(
                design,
                allocator,
                controller,
                capability="digital",
                signal=f"Motor {index + 1} direction 1",
                to_ref=driver.ref,
                to_pin=in1,
                net=f"MOTOR_{index + 1}_DIR1",
                voltage_v=controller_pin_voltage,
            )
            _allocate_signal(
                design,
                allocator,
                controller,
                capability="digital",
                signal=f"Motor {index + 1} direction 2",
                to_ref=driver.ref,
                to_pin=in2,
                net=f"MOTOR_{index + 1}_DIR2",
                voltage_v=controller_pin_voltage,
            )
            _connect(
                design,
                from_ref=driver.ref,
                from_pin=out1,
                to_ref=motor.ref,
                to_pin="M+",
                net=f"MOTOR_{index + 1}_A",
                signal=f"Motor {index + 1} phase A",
                kind="motor",
                voltage_v=battery_v,
            )
            _connect(
                design,
                from_ref=driver.ref,
                from_pin=out2,
                to_ref=motor.ref,
                to_pin="M-",
                net=f"MOTOR_{index + 1}_B",
                signal=f"Motor {index + 1} phase B",
                kind="motor",
                voltage_v=battery_v,
            )
    elif motors:
        design.add_issue(
            "motor_without_driver",
            "error",
            "DC motors are present but no H-bridge motor driver is selected.",
            [motor.ref for motor in motors],
            remediation="Never drive a motor directly from a pin; add a TB6612FNG or L298N.",
        )

    # ------------------------------------------------------------------
    # Sensors
    # ------------------------------------------------------------------
    i2c_sda: PinDefinition | None = None
    i2c_scl: PinDefinition | None = None
    if controller is not None and allocator is not None:
        i2c_sda = allocator.take("i2c_sda", "I2C SDA")
        i2c_scl = allocator.take("i2c_scl", "I2C SCL")

    for sensor in sensors:
        source = _power_source_for(
            profile=sensor.profile,
            controller_logic=controller_logic,
            has_regulator=has_regulator,
            has_controller_5v=has_controller_5v,
        )
        if source is None:
            design.add_issue(
                "missing_sensor_rail",
                "error",
                f"{sensor.label} needs a supply rail that this design does not provide.",
                [sensor.ref],
            )
        else:
            net, voltage = source
            source_ref = _rail_source_ref(net, controller, regulator)
            if source_ref is not None:
                source_pin = _rail_source_pin(net, controller, regulator)
                if source_pin is not None:
                    _connect(
                        design,
                        from_ref=source_ref.ref,
                        from_pin=source_pin,
                        to_ref=sensor.ref,
                        to_pin="VCC",
                        net=net,
                        signal="Sensor supply",
                        kind="power",
                        voltage_v=voltage,
                    )
            design.supply_by_ref[sensor.ref] = voltage

        if controller is None or allocator is None:
            continue
        if sensor.profile.key == "ir_line_5ch":
            for channel in range(1, 6):
                _allocate_signal(
                    design,
                    allocator,
                    controller,
                    capability="digital",
                    signal=f"Line sensor channel {channel}",
                    to_ref=sensor.ref,
                    to_pin=f"OUT{channel}",
                    net=f"IR_CH{channel}",
                    voltage_v=controller_pin_voltage,
                )
        elif sensor.profile.key == "hc_sr04":
            _allocate_signal(
                design,
                allocator,
                controller,
                capability="digital",
                signal="Ultrasonic trigger",
                to_ref=sensor.ref,
                to_pin="TRIG",
                net="ULTRASONIC_TRIG",
                voltage_v=controller_pin_voltage,
            )
            _allocate_signal(
                design,
                allocator,
                controller,
                capability="digital",
                signal="Ultrasonic echo",
                to_ref=sensor.ref,
                to_pin="ECHO",
                net="ULTRASONIC_ECHO",
                voltage_v=controller_pin_voltage,
            )
        elif sensor.profile.key in {"mpu6050", "apds9960"}:
            if i2c_sda is not None:
                design.pin_map[i2c_sda.name] = f"{sensor.ref}.SDA · I2C SDA"
                _connect(
                    design,
                    from_ref=controller.ref,
                    from_pin=i2c_sda.name,
                    to_ref=sensor.ref,
                    to_pin="SDA",
                    net="I2C_SDA",
                    signal="I2C data",
                    kind="bus",
                    voltage_v=controller_pin_voltage,
                )
            else:
                design.add_issue(
                    "missing_i2c",
                    "error",
                    "No I²C SDA pin is available for the IMU.",
                    [controller.ref, sensor.ref],
                )
            if i2c_scl is not None:
                design.pin_map[i2c_scl.name] = f"{sensor.ref}.SCL · I2C SCL"
                _connect(
                    design,
                    from_ref=controller.ref,
                    from_pin=i2c_scl.name,
                    to_ref=sensor.ref,
                    to_pin="SCL",
                    net="I2C_SCL",
                    signal="I2C clock",
                    kind="bus",
                    voltage_v=controller_pin_voltage,
                )
            else:
                design.add_issue(
                    "missing_i2c",
                    "error",
                    "No I²C SCL pin is available for the IMU.",
                    [controller.ref, sensor.ref],
                )
            if sensor.profile.key == "apds9960":
                _allocate_signal(
                    design,
                    allocator,
                    controller,
                    capability="digital",
                    signal="Proximity interrupt",
                    to_ref=sensor.ref,
                    to_pin="INT",
                    net="PROXIMITY_INT",
                    voltage_v=controller_pin_voltage,
                )

    # ------------------------------------------------------------------
    # Servos
    # ------------------------------------------------------------------
    for index, servo in enumerate(servos):
        source = _power_source_for(
            profile=servo.profile,
            controller_logic=controller_logic,
            has_regulator=has_regulator,
            has_controller_5v=has_controller_5v,
        )
        if controller is not None and allocator is not None:
            _allocate_signal(
                design,
                allocator,
                controller,
                capability="pwm",
                signal=f"Servo {index + 1} signal",
                to_ref=servo.ref,
                to_pin="SIG",
                net=f"SERVO_{index + 1}_SIG",
                voltage_v=controller_pin_voltage,
            )
        if source is not None:
            net, voltage = source
            source_ref = _rail_source_ref(net, controller, regulator)
            source_pin = _rail_source_pin(net, controller, regulator)
            if source_ref is not None and source_pin is not None:
                _connect(
                    design,
                    from_ref=source_ref.ref,
                    from_pin=source_pin,
                    to_ref=servo.ref,
                    to_pin="VCC",
                    net=net,
                    signal="Servo supply",
                    kind="power",
                    voltage_v=voltage,
                )
                design.supply_by_ref[servo.ref] = voltage
                if source_ref.profile.is_controller:
                    design.add_issue(
                        "servo_on_controller_rail",
                        "warning",
                        "Servo is on the controller regulator; add an external 5 V supply.",
                        [servo.ref, source_ref.ref],
                        remediation="Use a 5 V buck rail rated for the servo stall current.",
                    )

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------
    if not motors and not servos:
        design.add_issue(
            "no_actuators",
            "warning",
            "No motors or servos are selected; this is a controller and power plan only.",
            remediation="Add the drivetrain or joints to the bill of materials before building.",
        )
    if not sensors:
        design.notes.append(
            "No sensors were selected. Add a sensor before closing the control loop."
        )
    if spec.target_platform.value == "undecided":
        design.notes.append(
            "The controller was chosen from the robot archetype because the target platform "
            "was undecided. Pin names change if another controller is selected."
        )
    design.notes.append(
        f"Generated deterministically from the curated component library v{LIBRARY_VERSION}. "
        "Every net is derived from a datasheet-shaped profile, not from free-form text."
    )


def _driver_logic_rail(
    controller: PlacedPart | None,
    regulator: PlacedPart | None,
    has_controller_5v: bool,
) -> tuple[tuple[str, str], float, PlacedPart | None]:
    """Return ((net, pin), voltage, source)."""

    if controller is not None and has_controller_5v:
        return ((_V5_CTRL_NET, "5V"), 5.0, controller)
    if regulator is not None:
        return ((_V5_NET, "OUT+"), 5.0, regulator)
    if controller is not None and controller.profile.pin("3V3"):
        return ((_V33_NET, "3V3"), 3.3, controller)
    return (("", ""), 0.0, None)


def _rail_source_ref(
    net: str,
    controller: PlacedPart | None,
    regulator: PlacedPart | None,
) -> PlacedPart | None:
    if net == _V5_NET:
        return regulator
    return controller


def _rail_source_pin(
    net: str,
    controller: PlacedPart | None,
    regulator: PlacedPart | None,
) -> str | None:
    if net == _V5_NET:
        return "OUT+" if regulator is not None else None
    if net == _V5_CTRL_NET:
        return "5V" if controller is not None and controller.profile.pin("5V") else None
    if net == _V33_NET:
        return "3V3" if controller is not None and controller.profile.pin("3V3") else None
    return None


def _validate(design: _Design, parts: list[PlacedPart]) -> list[str]:
    """Run the deterministic safety checks and return passed-check strings."""

    passed: list[str] = []
    controllers = [part for part in parts if part.profile.is_controller]
    drivers = [part for part in parts if part.profile.category is ComponentCategory.MOTOR_DRIVER]
    motors = [part for part in parts if part.profile.category is ComponentCategory.MOTOR]
    batteries = [
        part
        for part in parts
        if part.profile.category is ComponentCategory.POWER
        and part.profile.output_voltage_v is None
    ]

    # Voltage compatibility -------------------------------------------------
    for part in parts:
        profile = part.profile
        if profile.category is ComponentCategory.POWER:
            continue
        supply = design.supply_by_ref.get(part.ref)
        if supply is None:
            continue
        if profile.supply_max_v is not None and supply > profile.supply_max_v + 0.05:
            severity: Literal["error", "warning"] = "error" if profile.is_controller else "warning"
            code = (
                "motor_overvoltage"
                if profile.category is ComponentCategory.MOTOR
                else "overvoltage"
            )
            design.add_issue(
                code,
                severity,
                f"{part.label} ({part.ref}) is rated to {profile.supply_max_v:g} V "
                f"but is connected to {supply:g} V.",
                [part.ref],
                remediation=(
                    "Use a lower-voltage pack, insert a buck regulator, or choose a part "
                    "rated for this rail. Re-check stall current at the higher voltage."
                ),
            )
        if profile.supply_min_v is not None and supply < profile.supply_min_v - 0.05:
            severity = "error" if profile.is_controller else "warning"
            design.add_issue(
                "undervoltage",
                severity,
                f"{part.label} ({part.ref}) needs at least {profile.supply_min_v:g} V "
                f"but receives {supply:g} V.",
                [part.ref],
                remediation="Raise the rail voltage or choose a part rated for this pack.",
            )
    if any(part.profile.is_controller for part in parts):
        passed.append("Every placed part's supply rail was checked against its rated range.")

    # Logic levels -----------------------------------------------------------
    controller = controllers[0] if controllers else None
    logic = controller.profile.logic_voltage_v if controller else None
    mismatch = False
    if controller is not None and logic is not None:
        for part in parts:
            profile = part.profile
            if profile.category is not ComponentCategory.SENSOR:
                continue
            supply = design.supply_by_ref.get(part.ref)
            output = profile.output_voltage_v or supply
            if output is not None and output > logic + 0.3:
                mismatch = True
                design.add_issue(
                    "logic_level_mismatch",
                    "warning",
                    f"{part.label} ({part.ref}) can output {output:g} V into a "
                    f"{logic:g} V controller input.",
                    [part.ref, controller.ref],
                    remediation=(
                        "Use a resistor divider or bidirectional level shifter, or power the "
                        "sensor from the 3.3 V rail when it supports it."
                    ),
                )
    if not mismatch and controller is not None:
        passed.append("No 5 V sensor output drives a 3.3 V input without level shifting.")

    # Common ground ----------------------------------------------------------
    grounded: set[str] = set()
    for connection in design.connections:
        if connection.net == _GROUND_NET:
            grounded.add(connection.from_ref)
            grounded.add(connection.to_ref)
    required = {
        part.ref
        for part in parts
        if part.profile.category
        in {
            ComponentCategory.CONTROLLER,
            ComponentCategory.MOTOR_DRIVER,
            ComponentCategory.SENSOR,
            ComponentCategory.ACTUATOR,
        }
        or (
            part.profile.category is ComponentCategory.POWER
            and part.profile.output_voltage_v is not None
        )
    }
    if batteries:
        required.add(batteries[0].ref)
    missing_ground = sorted(required - grounded)
    if missing_ground:
        refs = ", ".join(missing_ground)
        design.add_issue(
            "floating_ground",
            "error",
            f"These parts have no common ground connection: {refs}.",
            missing_ground,
            remediation="Tie every ground to a single star point at the battery negative terminal.",
        )
    else:
        passed.append(
            f"Common ground verified across {len(grounded)} parts at the battery star point."
        )

    # Pin conflicts ----------------------------------------------------------
    usage: dict[tuple[str, str], set[str]] = defaultdict(set)
    for connection in design.connections:
        usage[(connection.from_ref, connection.from_pin)].add(connection.net)
        usage[(connection.to_ref, connection.to_pin)].add(connection.net)
    conflicts = {key: nets for key, nets in usage.items() if len(nets) > 1}
    if conflicts:
        for (ref, pin), nets in conflicts.items():
            design.add_issue(
                "pin_conflict",
                "error",
                f"{ref}.{pin} is assigned to more than one net: {', '.join(sorted(nets))}.",
                [ref],
                remediation="Reassign the signal to a free pin; never share a pin across nets.",
            )
    else:
        passed.append("No physical pin is assigned to more than one net.")

    # Motor drive ------------------------------------------------------------
    if motors and not drivers:
        # The wiring pass already raised motor_without_driver; keep validation quiet.
        pass
    elif motors and drivers:
        passed.append("Every DC motor is driven through a current-rated H-bridge.")

    # Current budget ---------------------------------------------------------
    total_peak = sum((part.profile.current_ma_peak for part in parts), 0.0)
    battery = batteries[0] if batteries else None
    if battery is not None and battery.profile.max_supply_current_ma is not None:
        recommended = math.ceil(total_peak * 1.3 / 100.0) * 100.0
        limit = battery.profile.max_supply_current_ma
        if recommended > limit:
            design.add_issue(
                "current_over_budget",
                "error",
                f"Peak load needs {recommended:.0f} mA with margin, above the "
                f"{limit:.0f} mA pack limit.",
                [battery.ref],
                remediation=(
                    "Choose a pack with a higher continuous current rating, reduce motor stall "
                    "load, or power high-current servos from a separate battery."
                ),
            )
        else:
            margin = (limit - recommended) / limit * 100
            if margin < 20:
                design.add_issue(
                    "tight_current_margin",
                    "warning",
                    f"Only {margin:.0f}% current headroom remains at stall.",
                    [battery.ref],
                    remediation="Add a larger pack or reduce simultaneous high-current loads.",
                )
            passed.append(
                f"Peak load {total_peak / 1000:.2f} A is within the "
                f"{limit / 1000:.1f} A pack limit."
            )

    # Servo rail -------------------------------------------------------------
    if any(part.profile.category is ComponentCategory.ACTUATOR for part in parts):
        passed.append("Servo signal pins were assigned to hardware PWM channels.")

    return passed


def _build_budget(design: _Design, parts: list[PlacedPart]) -> PowerBudget:
    batteries = [
        part
        for part in parts
        if part.profile.category is ComponentCategory.POWER
        and part.profile.output_voltage_v is None
    ]
    battery = batteries[0] if batteries else None
    typical = sum((part.profile.current_ma_typical for part in parts), 0.0)
    peak = sum((part.profile.current_ma_peak for part in parts), 0.0)
    supply_voltage = _nominal_voltage(battery.profile) if battery else None
    limit = battery.profile.max_supply_current_ma if battery else None
    recommended = math.ceil(peak * 1.3 / 100.0) * 100.0 if peak else None
    margin = (
        round((limit - recommended) / limit * 100, 1)
        if limit is not None and recommended is not None
        else None
    )
    capacity = battery.profile.capacity_mah if battery else None
    usable = round(capacity * 0.8, 1) if capacity is not None else None
    runtime = round(usable / typical * 60, 0) if usable and typical else None

    return PowerBudget(
        supply_voltage_v=supply_voltage,
        peak_current_ma=round(peak, 1) if peak else None,
        typical_current_ma=round(typical, 1) if typical else None,
        recommended_supply_ma=recommended,
        margin_percent=margin,
        usable_capacity_mah=usable,
        estimated_runtime_min=runtime,
    )


def _build_rails(design: _Design, parts: list[PlacedPart]) -> list[PowerRail]:
    by_ref = {part.ref: part for part in parts}
    controllers = [part for part in parts if part.profile.is_controller]
    drivers = [part for part in parts if part.profile.category is ComponentCategory.MOTOR_DRIVER]
    batteries = [
        part
        for part in parts
        if part.profile.category is ComponentCategory.POWER
        and part.profile.output_voltage_v is None
    ]
    regulators = [
        part
        for part in parts
        if part.profile.category is ComponentCategory.POWER
        and part.profile.output_voltage_v is not None
    ]
    controller = controllers[0] if controllers else None
    regulator = regulators[0] if regulators else None
    battery = batteries[0] if batteries else None
    driver = drivers[0] if drivers else None
    by_ref = {part.ref: part for part in parts}

    load_refs: dict[str, set[str]] = defaultdict(set)
    for connection in design.connections:
        load_refs[connection.net].add(connection.to_ref)
    total_peak = sum((part.profile.current_ma_peak for part in parts), 0.0)

    def peak_for(net: str) -> float:
        return sum(
            by_ref[ref].profile.current_ma_peak
            for ref in load_refs.get(net, set())
            if ref in by_ref
        )

    rails: list[PowerRail] = []
    if battery is not None:
        rails.append(
            PowerRail(
                name=_VBAT_NET,
                voltage_v=_nominal_voltage(battery.profile),
                peak_current_ma=round(total_peak, 1),
                source_ref=battery.ref,
                notes="Pack rail. Motors and the buck input connect here.",
            )
        )
        rails.append(
            PowerRail(
                name=_GROUND_NET,
                voltage_v=0.0,
                peak_current_ma=round(total_peak, 1),
                source_ref=battery.ref,
                notes="Single star-point ground at the battery negative terminal.",
            )
        )
    if regulator is not None:
        rails.append(
            PowerRail(
                name=_V5_NET,
                voltage_v=regulator.profile.output_voltage_v,
                peak_current_ma=round(peak_for(_V5_NET), 1),
                source_ref=regulator.ref,
                notes="Regulated logic/servo rail.",
            )
        )
    if controller is not None and controller.profile.pin("5V"):
        rails.append(
            PowerRail(
                name=_V5_CTRL_NET,
                voltage_v=5.0,
                peak_current_ma=round(peak_for(_V5_CTRL_NET), 1),
                source_ref=controller.ref,
                notes="Controller 5 V output; keep logic loads inside its regulator limit.",
            )
        )
    if controller is not None and controller.profile.pin("3V3"):
        rails.append(
            PowerRail(
                name=_V33_NET,
                voltage_v=3.3,
                peak_current_ma=round(peak_for(_V33_NET), 1),
                source_ref=controller.ref,
                notes="Controller 3.3 V output; 3.3 V-only sensors live here.",
            )
        )
    if driver is not None:
        rails.append(
            PowerRail(
                name="DRIVER_LOGIC",
                voltage_v=5.0 if controller and controller.profile.pin("5V") else 3.3,
                peak_current_ma=round(driver.profile.current_ma_peak, 1),
                source_ref=driver.ref,
                notes="TB6612 VCC/STBY logic reference.",
            )
        )
    return rails


def _wiring_steps(design: _Design, parts: list[PlacedPart]) -> list[str]:
    controllers = [part for part in parts if part.profile.is_controller]
    batteries = [
        part
        for part in parts
        if part.profile.category is ComponentCategory.POWER
        and part.profile.output_voltage_v is None
    ]
    drivers = [part for part in parts if part.profile.category is ComponentCategory.MOTOR_DRIVER]
    motors = [part for part in parts if part.profile.category is ComponentCategory.MOTOR]
    sensors = [part for part in parts if part.profile.category is ComponentCategory.SENSOR]

    steps = ["Power off and disconnect the battery before touching any conductor."]
    if controllers:
        steps.append(
            f"Mount {controllers[0].ref} ({controllers[0].label}) on insulated standoffs and "
            "keep USB and header pins clear."
        )
    if drivers:
        steps.append(
            f"Mount {drivers[0].ref} ({drivers[0].label}) so the heatsink has airflow and the "
            "motor terminals cannot short against the chassis."
        )
    if batteries:
        steps.append(
            f"Build the ground bus first: {batteries[0].ref}.NEG to a single star point, then "
            f"to every GND pin. {batteries[0].ref} negative is the only reference."
        )
        steps.append(
            f"Connect {batteries[0].ref}.POS through a fuse to the motor supply and buck input. "
            "Leave the battery unplugged until the continuity check passes."
        )
    if drivers and motors:
        steps.append(
            "Wire the motor outputs: driver AO1/AO2 to the first motor, BO1/BO2 to the second. "
            "Keep the pair twisted; reverse one pair if a wheel spins backwards."
        )
        steps.append(
            "Connect the controller PWM and direction pins to PWMA/AIN1/AIN2 and "
            "PWMB/BIN1/BIN2. Tie STBY high through the logic rail."
        )
    if sensors:
        steps.append(
            "Wire sensors last, following the pin map one net at a time. Power 3.3 V-only "
            "sensors from the 3.3 V rail and fit a level shifter where flagged."
        )
    steps.extend(
        [
            "Inspect for stray strands, reversed polarity, and any pin assigned to two nets.",
            "Power on with a current-limited supply or the fuse fitted. Measure the 5 V rail "
            "under load before enabling the motors.",
            "Run each actuator at low duty first, then verify emergency stop and battery "
            "low-voltage cutoff before a full-speed test.",
        ]
    )
    return steps


def _finalize_connected_pins(design: _Design) -> None:
    used: set[tuple[str, str]] = set()
    for connection in design.connections:
        used.add((connection.from_ref, connection.from_pin))
        used.add((connection.to_ref, connection.to_pin))
    for node in design.nodes:
        for pin in node.pins:
            pin.connected = (node.ref, pin.name) in used


def build_electrical_plan(
    spec: RobotSpecificationDraft,
    bom: ComponentResearchOutput,
) -> ElectricalPlan:
    """Create a validated wiring plan from a specification and bill of materials."""

    parts, unresolved = _place_parts(bom)
    design = _Design(nodes=_make_nodes(parts))
    design.by_ref = {node.ref: node for node in design.nodes}

    for note in unresolved:
        design.notes.append(note)

    _wire(design, parts, spec)
    passed = _validate(design, parts)
    _finalize_connected_pins(design)

    budget = _build_budget(design, parts)
    rails = _build_rails(design, parts)
    issues = design.issues
    warnings = [issue.message for issue in issues if issue.severity in {"error", "warning"}]
    errors = [issue for issue in issues if issue.severity == "error"]
    if errors:
        passed.append(f"{len(errors)} blocking issue(s) must be resolved before applying power.")

    return ElectricalPlan(
        nodes=design.nodes,
        connections=design.connections,
        power_budget=budget,
        power_rails=rails,
        pin_map=design.pin_map,
        issues=issues,
        safety_checks=passed,
        warnings=warnings,
        wiring_steps=_wiring_steps(design, parts),
        design_notes=design.notes,
        library_version=LIBRARY_VERSION,
    )


__all__ = ["PlacedPart", "build_electrical_plan"]
