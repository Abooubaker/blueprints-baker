"""Curated component library used by the deterministic planning agents.

The library is intentionally small, explicit, and datasheet-shaped. It is not a
parts database: it is the electrical truth the wiring engine reasons about.
Every profile carries the data needed to make one decision — pin names, supply
range, logic level, and current draw — so validation never relies on prose.

Sources for the values are the vendor datasheets and common breakout-board
documentation. Values are conservative and rounded; they are planning inputs,
not a substitute for the final datasheet check.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from app.models.enums import ComponentCategory, RobotType

PinKind = Literal[
    "power",
    "ground",
    "gpio",
    "pwm",
    "adc",
    "i2c_sda",
    "i2c_scl",
    "uart_tx",
    "uart_rx",
    "motor_out",
    "motor_in",
    "analog",
    "other",
]


@dataclass(frozen=True, slots=True)
class PinDefinition:
    """A single physical pin on a component."""

    name: str
    kind: PinKind
    voltage_v: float | None = None
    capabilities: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True, slots=True)
class ComponentProfile:
    """Electrical facts for one selectable part."""

    key: str
    name: str
    category: ComponentCategory
    role: str
    manufacturer: str
    model_number: str
    price_usd: Decimal
    supply_min_v: float | None
    supply_max_v: float | None
    logic_voltage_v: float | None
    current_ma_typical: float
    current_ma_peak: float
    pins: tuple[PinDefinition, ...]
    interfaces: tuple[str, ...] = ()
    notes: str = ""
    max_supply_current_ma: float | None = None
    output_voltage_v: float | None = None
    nominal_voltage_v: float | None = None
    capacity_mah: float | None = None

    def pin(self, name: str) -> PinDefinition | None:
        for pin in self.pins:
            if pin.name == name:
                return pin
        return None

    @property
    def is_controller(self) -> bool:
        return self.category is ComponentCategory.CONTROLLER


def _pin(name: str, kind: PinKind, voltage: float | None = None, *caps: str) -> PinDefinition:
    return PinDefinition(name=name, kind=kind, voltage_v=voltage, capabilities=caps)


def _controller_pins(
    prefixes: tuple[str, ...],
    *,
    logic: float,
    pwm: set[str],
    adc: set[str],
    i2c: tuple[str, str],
) -> tuple[PinDefinition, ...]:
    pins: list[PinDefinition] = [
        _pin("VIN", "power"),
        _pin("3V3", "power", 3.3),
        _pin("GND", "ground", 0.0),
    ]
    if logic == 5.0:
        pins.append(_pin("5V", "power", 5.0))
    for name in prefixes:
        caps: list[str] = ["digital"]
        if name in pwm:
            caps.append("pwm")
        if name in adc:
            caps.append("analog")
        if name == i2c[0]:
            caps.append("i2c_sda")
        if name == i2c[1]:
            caps.append("i2c_scl")
        pins.append(
            PinDefinition(
                name=name,
                kind=("i2c_sda" if name == i2c[0] else "i2c_scl" if name == i2c[1] else "gpio"),
                voltage_v=logic,
                capabilities=tuple(caps),
            )
        )
    return tuple(pins)


_ARDUINO_DIGITAL = tuple(f"D{n}" for n in range(2, 14))
_ESP32_GPIO = (
    "GPIO4",
    "GPIO5",
    "GPIO13",
    "GPIO14",
    "GPIO15",
    "GPIO16",
    "GPIO17",
    "GPIO18",
    "GPIO19",
    "GPIO21",
    "GPIO22",
    "GPIO23",
    "GPIO25",
    "GPIO26",
    "GPIO27",
    "GPIO32",
    "GPIO33",
)
_PICO_GPIO = tuple(f"GP{g}" for g in range(0, 23) if g != 3)


def _esp32_pins() -> tuple[PinDefinition, ...]:
    pins: list[PinDefinition] = [
        _pin("VIN", "power"),
        _pin("3V3", "power", 3.3),
        _pin("GND", "ground", 0.0),
    ]
    for name in _ESP32_GPIO:
        caps: list[str] = ["digital", "pwm"]
        if name in {"GPIO32", "GPIO33"}:
            caps.append("analog")
        if name == "GPIO21":
            caps.append("i2c_sda")
        if name == "GPIO22":
            caps.append("i2c_scl")
        pins.append(
            PinDefinition(
                name=name,
                kind=("i2c_sda" if name == "GPIO21" else "i2c_scl" if name == "GPIO22" else "gpio"),
                voltage_v=3.3,
                capabilities=tuple(caps),
            )
        )
    return tuple(pins)


def _pico_pins() -> tuple[PinDefinition, ...]:
    pins: list[PinDefinition] = [
        _pin("VSYS", "power"),
        _pin("3V3", "power", 3.3),
        _pin("GND", "ground", 0.0),
    ]
    for name in _PICO_GPIO:
        caps: list[str] = ["digital", "pwm", "analog"]
        if name == "GP4":
            caps.append("i2c_sda")
        if name == "GP5":
            caps.append("i2c_scl")
        pins.append(
            PinDefinition(
                name=name,
                kind=("i2c_sda" if name == "GP4" else "i2c_scl" if name == "GP5" else "gpio"),
                voltage_v=3.3,
                capabilities=tuple(caps),
            )
        )
    return tuple(pins)


COMPONENT_LIBRARY: dict[str, ComponentProfile] = {
    # ------------------------------------------------------------------
    # Controllers
    # ------------------------------------------------------------------
    "arduino_uno": ComponentProfile(
        key="arduino_uno",
        name="Arduino Uno R3",
        category=ComponentCategory.CONTROLLER,
        role="controller",
        manufacturer="Arduino",
        model_number="A000066",
        price_usd=Decimal("27.60"),
        supply_min_v=7.0,
        supply_max_v=12.0,
        logic_voltage_v=5.0,
        current_ma_typical=50.0,
        current_ma_peak=100.0,
        pins=_controller_pins(
            _ARDUINO_DIGITAL + tuple(f"A{n}" for n in range(6)),
            logic=5.0,
            pwm={"D3", "D5", "D6", "D9", "D10", "D11"},
            adc={f"A{n}" for n in range(6)},
            i2c=("A4", "A5"),
        ),
        interfaces=("gpio", "pwm", "adc", "i2c", "uart"),
        notes="5 V logic. VIN accepts 7-12 V; never power the 5 V pin and VIN together.",
    ),
    "esp32_devkit": ComponentProfile(
        key="esp32_devkit",
        name="ESP32 DevKit V1",
        category=ComponentCategory.CONTROLLER,
        role="controller",
        manufacturer="Espressif",
        model_number="ESP32-DEVKITC-32D",
        price_usd=Decimal("9.50"),
        supply_min_v=4.5,
        supply_max_v=6.0,
        logic_voltage_v=3.3,
        current_ma_typical=80.0,
        current_ma_peak=240.0,
        pins=_esp32_pins(),
        interfaces=("gpio", "pwm", "adc", "i2c", "uart", "wifi", "bluetooth"),
        notes="3.3 V logic. Power VIN from a regulated 5 V rail; inputs are not 5 V tolerant.",
    ),
    "pico": ComponentProfile(
        key="pico",
        name="Raspberry Pi Pico",
        category=ComponentCategory.CONTROLLER,
        role="controller",
        manufacturer="Raspberry Pi",
        model_number="SC0915",
        price_usd=Decimal("8.00"),
        supply_min_v=1.8,
        supply_max_v=5.5,
        logic_voltage_v=3.3,
        current_ma_typical=30.0,
        current_ma_peak=80.0,
        pins=_pico_pins(),
        interfaces=("gpio", "pwm", "adc", "i2c", "uart"),
        notes="3.3 V logic. VSYS accepts 1.8-5.5 V; do not feed 5 V into a GPIO.",
    ),
    # ------------------------------------------------------------------
    # Motor drivers and motors
    # ------------------------------------------------------------------
    "tb6612fng": ComponentProfile(
        key="tb6612fng",
        name="TB6612FNG dual motor driver",
        category=ComponentCategory.MOTOR_DRIVER,
        role="motor_driver",
        manufacturer="Toshiba",
        model_number="TB6612FNG",
        price_usd=Decimal("6.20"),
        supply_min_v=2.5,
        supply_max_v=13.5,
        logic_voltage_v=None,
        current_ma_typical=2.0,
        current_ma_peak=10.0,
        pins=(
            _pin("VM", "power"),
            _pin("VCC", "power"),
            _pin("GND", "ground", 0.0),
            _pin("STBY", "gpio"),
            _pin("AIN1", "gpio"),
            _pin("AIN2", "gpio"),
            _pin("PWMA", "gpio"),
            _pin("BIN1", "gpio"),
            _pin("BIN2", "gpio"),
            _pin("PWMB", "gpio"),
            _pin("AO1", "motor_out"),
            _pin("AO2", "motor_out"),
            _pin("BO1", "motor_out"),
            _pin("BO2", "motor_out"),
        ),
        interfaces=("pwm", "gpio"),
        notes="1.2 A continuous per channel; heatsink above 0.8 A. STBY must be pulled high.",
    ),
    "l298n": ComponentProfile(
        key="l298n",
        name="L298N dual H-bridge",
        category=ComponentCategory.MOTOR_DRIVER,
        role="motor_driver",
        manufacturer="STMicroelectronics",
        model_number="L298N",
        price_usd=Decimal("6.80"),
        supply_min_v=5.0,
        supply_max_v=35.0,
        logic_voltage_v=5.0,
        current_ma_typical=20.0,
        current_ma_peak=20.0,
        pins=(
            _pin("VMS", "power"),
            _pin("5V", "power", 5.0),
            _pin("GND", "ground", 0.0),
            _pin("ENA", "gpio"),
            _pin("IN1", "gpio"),
            _pin("IN2", "gpio"),
            _pin("IN3", "gpio"),
            _pin("IN4", "gpio"),
            _pin("ENB", "gpio"),
            _pin("OUT1", "motor_out"),
            _pin("OUT2", "motor_out"),
            _pin("OUT3", "motor_out"),
            _pin("OUT4", "motor_out"),
        ),
        interfaces=("pwm", "gpio"),
        notes=(
            "2 A continuous per channel with a heatsink. Remove the 5 V jumper "
            "when using an external 5 V rail."
        ),
    ),
    "n20_6v": ComponentProfile(
        key="n20_6v",
        name="N20 gear motor (6 V)",
        category=ComponentCategory.MOTOR,
        role="drive_motor",
        manufacturer="Generic",
        model_number="N20-6V-100RPM",
        price_usd=Decimal("5.40"),
        supply_min_v=3.0,
        supply_max_v=6.0,
        logic_voltage_v=None,
        current_ma_typical=100.0,
        current_ma_peak=700.0,
        pins=(_pin("M+", "motor_in"), _pin("M-", "motor_in")),
        interfaces=("dc_motor",),
        notes=(
            "Stall current is much higher than the no-load rating. Never connect "
            "directly to a controller pin."
        ),
    ),
    "tt_motor_6v": ComponentProfile(
        key="tt_motor_6v",
        name="TT gear motor (6 V)",
        category=ComponentCategory.MOTOR,
        role="drive_motor",
        manufacturer="Generic",
        model_number="TT-6V-200RPM",
        price_usd=Decimal("3.20"),
        supply_min_v=3.0,
        supply_max_v=6.0,
        logic_voltage_v=None,
        current_ma_typical=150.0,
        current_ma_peak=1200.0,
        pins=(_pin("M+", "motor_in"), _pin("M-", "motor_in")),
        interfaces=("dc_motor",),
        notes="Budget gearbox; stall current is high and the gearbox is noisy under load.",
    ),
    "sg90": ComponentProfile(
        key="sg90",
        name="SG90 micro servo",
        category=ComponentCategory.ACTUATOR,
        role="servo",
        manufacturer="TowerPro",
        model_number="SG90",
        price_usd=Decimal("3.40"),
        supply_min_v=4.8,
        supply_max_v=6.0,
        logic_voltage_v=None,
        current_ma_typical=100.0,
        current_ma_peak=650.0,
        pins=(
            _pin("VCC", "power"),
            _pin("GND", "ground", 0.0),
            _pin("SIG", "gpio"),
        ),
        interfaces=("pwm",),
        notes=(
            "Power servos from a separate 5 V rail, not the controller's regulator. "
            "Add a bulk capacitor."
        ),
    ),
    # ------------------------------------------------------------------
    # Sensors
    # ------------------------------------------------------------------
    "ir_line_5ch": ComponentProfile(
        key="ir_line_5ch",
        name="5-channel IR line sensor",
        category=ComponentCategory.SENSOR,
        role="line_sensor",
        manufacturer="Generic",
        model_number="TCRT5000-5CH",
        price_usd=Decimal("4.80"),
        supply_min_v=3.3,
        supply_max_v=5.0,
        logic_voltage_v=None,
        current_ma_typical=20.0,
        current_ma_peak=40.0,
        pins=(
            _pin("VCC", "power"),
            _pin("GND", "ground", 0.0),
            *(_pin(f"OUT{n}", "gpio") for n in range(1, 6)),
        ),
        interfaces=("digital",),
        notes="Outputs follow VCC. Power at 3.3 V when using a 3.3 V controller.",
    ),
    "hc_sr04": ComponentProfile(
        key="hc_sr04",
        name="HC-SR04 ultrasonic rangefinder",
        category=ComponentCategory.SENSOR,
        role="distance_sensor",
        manufacturer="Generic",
        model_number="HC-SR04",
        price_usd=Decimal("2.30"),
        supply_min_v=4.5,
        supply_max_v=5.5,
        logic_voltage_v=None,
        current_ma_typical=15.0,
        current_ma_peak=20.0,
        pins=(
            _pin("VCC", "power"),
            _pin("TRIG", "gpio"),
            _pin("ECHO", "gpio"),
            _pin("GND", "ground", 0.0),
        ),
        interfaces=("digital",),
        output_voltage_v=5.0,
        notes="ECHO is a 5 V output. Use a divider or level shifter with 3.3 V logic.",
    ),
    "mpu6050": ComponentProfile(
        key="mpu6050",
        name="MPU-6050 IMU",
        category=ComponentCategory.SENSOR,
        role="imu",
        manufacturer="TDK InvenSense",
        model_number="MPU-6050",
        price_usd=Decimal("3.90"),
        supply_min_v=3.3,
        supply_max_v=5.0,
        logic_voltage_v=3.3,
        current_ma_typical=4.0,
        current_ma_peak=6.0,
        pins=(
            _pin("VCC", "power"),
            _pin("GND", "ground", 0.0),
            _pin("SDA", "i2c_sda", 3.3),
            _pin("SCL", "i2c_scl", 3.3),
        ),
        interfaces=("i2c",),
        notes=(
            "I2C address 0x68 (0x69 with AD0 high). Add 4.7 kohm pull-ups only if "
            "the breakout lacks them."
        ),
    ),
    "apds9960": ComponentProfile(
        key="apds9960",
        name="APDS-9960 proximity sensor",
        category=ComponentCategory.SENSOR,
        role="proximity_sensor",
        manufacturer="Broadcom",
        model_number="APDS-9960",
        price_usd=Decimal("5.10"),
        supply_min_v=3.3,
        supply_max_v=3.6,
        logic_voltage_v=3.3,
        current_ma_typical=3.0,
        current_ma_peak=5.0,
        pins=(
            _pin("VCC", "power"),
            _pin("GND", "ground", 0.0),
            _pin("SDA", "i2c_sda", 3.3),
            _pin("SCL", "i2c_scl", 3.3),
            _pin("INT", "gpio"),
        ),
        interfaces=("i2c",),
        notes="3.3 V only. Useful for gesture and short-range obstacle detection.",
    ),
    # ------------------------------------------------------------------
    # Power
    # ------------------------------------------------------------------
    "battery_2s_lipo": ComponentProfile(
        key="battery_2s_lipo",
        name="2S LiPo battery (7.4 V, 2200 mAh)",
        category=ComponentCategory.POWER,
        role="battery",
        manufacturer="Generic",
        model_number="2S-2200",
        price_usd=Decimal("18.00"),
        supply_min_v=6.0,
        supply_max_v=8.4,
        logic_voltage_v=None,
        current_ma_typical=0.0,
        current_ma_peak=0.0,
        pins=(_pin("POS", "power"), _pin("NEG", "ground", 0.0)),
        interfaces=("jst_xh",),
        max_supply_current_ma=5000.0,
        nominal_voltage_v=7.4,
        capacity_mah=2200.0,
        notes=(
            "Nominal 7.4 V, 8.4 V full charge. Use a fused XT30/JST connector and "
            "a low-voltage alarm."
        ),
    ),
    "battery_4xaa": ComponentProfile(
        key="battery_4xaa",
        name="4xAA battery holder (6 V)",
        category=ComponentCategory.POWER,
        role="battery",
        manufacturer="Generic",
        model_number="4AA",
        price_usd=Decimal("2.80"),
        supply_min_v=4.8,
        supply_max_v=6.4,
        logic_voltage_v=None,
        current_ma_typical=0.0,
        current_ma_peak=0.0,
        pins=(_pin("POS", "power"), _pin("NEG", "ground", 0.0)),
        interfaces=("wire_leads",),
        max_supply_current_ma=2000.0,
        nominal_voltage_v=6.0,
        capacity_mah=2000.0,
        notes="Alkaline cells sag under motor load. Use NiMH cells for repeatable behaviour.",
    ),
    "buck_5v_3a": ComponentProfile(
        key="buck_5v_3a",
        name="5 V 3 A buck converter",
        category=ComponentCategory.POWER,
        role="regulator",
        manufacturer="Generic",
        model_number="MP1584EN-5V",
        price_usd=Decimal("4.20"),
        supply_min_v=6.0,
        supply_max_v=24.0,
        logic_voltage_v=None,
        current_ma_typical=5.0,
        current_ma_peak=10.0,
        pins=(
            _pin("IN+", "power"),
            _pin("IN-", "ground", 0.0),
            _pin("OUT+", "power"),
            _pin("OUT-", "ground", 0.0),
        ),
        interfaces=("screw_terminal",),
        output_voltage_v=5.0,
        nominal_voltage_v=5.0,
        max_supply_current_ma=3000.0,
        notes="Set the output to 5.0 V before connecting logic. Verify with a meter under load.",
    ),
}

# Which profiles are electrically compatible with which robot archetype.
REFERENCE_DESIGNS: dict[RobotType, tuple[str, ...]] = {
    RobotType.LINE_FOLLOWER: ("tb6612fng", "n20_6v", "ir_line_5ch", "battery_2s_lipo"),
    RobotType.OBSTACLE_AVOIDER: (
        "tb6612fng",
        "n20_6v",
        "hc_sr04",
        "sg90",
        "battery_2s_lipo",
        "buck_5v_3a",
    ),
    RobotType.ROVER: (
        "tb6612fng",
        "n20_6v",
        "hc_sr04",
        "mpu6050",
        "battery_2s_lipo",
        "buck_5v_3a",
    ),
    RobotType.ROBOT_ARM: ("sg90", "battery_2s_lipo", "buck_5v_3a"),
    RobotType.BALANCING_BOT: (
        "tb6612fng",
        "n20_6v",
        "mpu6050",
        "battery_2s_lipo",
        "buck_5v_3a",
    ),
}

UNSUPPORTED_ROBOT_TYPES: dict[RobotType, str] = {
    RobotType.DRONE: (
        "Drone power distribution and brushless ESCs are outside the validated "
        "library. Add the airframe, ESC, and flight-controller profiles first."
    ),
}


def choose_controller_key(robot_type: RobotType, target_platform: str, difficulty: str) -> str:
    """Pick a controller deterministically from the project's stated preference."""

    platform = target_platform.lower()
    if platform == "esp32":
        return "esp32_devkit"
    if platform == "raspberry_pi":
        return "pico"
    if platform == "arduino":
        return "arduino_uno"
    if robot_type in {RobotType.ROVER, RobotType.BALANCING_BOT} and difficulty == "advanced":
        return "esp32_devkit"
    return "arduino_uno"


def reference_part_keys(
    robot_type: RobotType,
    *,
    controller_key: str,
    drive_type: str = "none",
) -> tuple[list[str], list[str]]:
    """Return (profile keys, unresolved requirements) for an archetype."""

    unresolved: list[str] = []
    if robot_type in UNSUPPORTED_ROBOT_TYPES:
        unresolved.append(UNSUPPORTED_ROBOT_TYPES[robot_type])
        return [controller_key, "battery_2s_lipo", "buck_5v_3a"], unresolved

    keys = list(REFERENCE_DESIGNS.get(robot_type, ()))
    if robot_type is RobotType.CUSTOM:
        if drive_type in {"differential", "tank", "mecanum", "omni"}:
            keys = ["tb6612fng", "n20_6v", "battery_2s_lipo"]
        elif drive_type == "servo_arm":
            keys = ["sg90", "sg90", "sg90", "battery_2s_lipo", "buck_5v_3a"]
        else:
            keys = ["battery_2s_lipo", "buck_5v_3a"]
            unresolved.append(
                "Custom robot has no drive architecture. Add actuators and sensors to "
                "the bill of materials before finalising the wiring."
            )

    if controller_key in {"esp32_devkit", "pico"} and "buck_5v_3a" not in keys:
        keys.append("buck_5v_3a")
    return [controller_key, *keys], unresolved


@dataclass(frozen=True, slots=True)
class ReferencePart:
    profile: ComponentProfile
    role: str
    quantity: int
    rationale: str


_ROLE_OVERRIDES: dict[str, str] = {
    "tb6612fng": "motor_driver",
    "l298n": "motor_driver",
    "n20_6v": "drive_motor",
    "tt_motor_6v": "drive_motor",
    "ir_line_5ch": "line_sensor",
    "hc_sr04": "distance_sensor",
    "mpu6050": "imu",
    "apds9960": "proximity_sensor",
    "sg90": "servo",
    "battery_2s_lipo": "battery",
    "battery_4xaa": "battery",
    "buck_5v_3a": "regulator",
}

_ROLE_RATIONALE: dict[str, str] = {
    "controller": "Runs the control loop and exposes the GPIO/PWM/I2C pins used below.",
    "motor_driver": "Provides the current gain and flyback protection a motor needs.",
    "drive_motor": "Selected for the wheeled drivetrain in this robot archetype.",
    "line_sensor": "Five downward channels give a usable position error for line following.",
    "distance_sensor": "Adds a forward obstacle/distance measurement.",
    "imu": "Provides orientation and acceleration feedback for closed-loop control.",
    "proximity_sensor": "Adds short-range gesture and proximity sensing.",
    "servo": "Provides one positional degree of freedom.",
    "battery": "Supplies the pack voltage; the engine validates it against every load.",
    "regulator": "Creates a stable 5 V rail for logic and servos.",
}


def build_reference_bom(
    *,
    robot_type: RobotType,
    target_platform: str,
    difficulty: str,
    drive_type: str,
    budget_max_usd: Decimal | None = None,
) -> tuple[list[ReferencePart], list[str]]:
    """Build the curated reference bill of materials for a robot archetype."""

    controller_key = choose_controller_key(robot_type, target_platform, difficulty)
    keys, unresolved = reference_part_keys(
        robot_type, controller_key=controller_key, drive_type=drive_type
    )

    counts: dict[str, int] = {}
    for key in keys:
        if key not in COMPONENT_LIBRARY:
            unresolved.append(f"Component profile '{key}' is missing from the library.")
            continue
        counts[key] = counts.get(key, 0) + 1

    # Differential drive needs two motors; a servo arm needs three joints.
    if "n20_6v" in counts:
        counts["n20_6v"] = 2
    if "tt_motor_6v" in counts:
        counts["tt_motor_6v"] = 2
    if robot_type is RobotType.ROBOT_ARM and "sg90" in counts:
        counts["sg90"] = 3

    parts: list[ReferencePart] = []
    for key, quantity in counts.items():
        profile = COMPONENT_LIBRARY[key]
        role = "controller" if profile.is_controller else _ROLE_OVERRIDES.get(key, profile.role)
        parts.append(
            ReferencePart(
                profile=profile,
                role=role,
                quantity=quantity,
                rationale=_ROLE_RATIONALE.get(role, profile.notes),
            )
        )

    total = sum((part.profile.price_usd * part.quantity for part in parts), Decimal("0"))
    if budget_max_usd is not None and total > budget_max_usd:
        unresolved.append(
            f"Reference components total ${total:.2f}, above the ${budget_max_usd:.2f} budget. "
            "Substitute lower-cost parts in the bill of materials."
        )

    return parts, unresolved


__all__ = [
    "COMPONENT_LIBRARY",
    "REFERENCE_DESIGNS",
    "UNSUPPORTED_ROBOT_TYPES",
    "ComponentProfile",
    "PinDefinition",
    "ReferencePart",
    "build_reference_bom",
    "choose_controller_key",
    "reference_part_keys",
]
