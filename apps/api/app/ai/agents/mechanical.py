"""Mechanical Design Agent — parametric chassis, weight, and print price.

The 3D model is intentionally basic: a rectangular chassis plate exported as an
ASCII STL. Its purpose is to estimate material weight and price with the
required JOD print chart, not to replace a real CAD review. Onshape or another
free tool can import the STL later; no account or network access is required.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from app.ai.base import BaseAgent
from app.ai.contracts import (
    AgentRequest,
    AssemblyStep,
    Dimensions,
    MechanicalInput,
    MechanicalOutput,
    MechanicalPart,
    PrintMaterialQuote,
)
from app.models.enums import AgentName, PrintMaterial, RobotType
from app.pricing import material_fraction_for_infill, price_print

_DEFAULT_SIZE: dict[RobotType, tuple[Decimal, Decimal, Decimal]] = {
    RobotType.LINE_FOLLOWER: (Decimal("120"), Decimal("90"), Decimal("4")),
    RobotType.OBSTACLE_AVOIDER: (Decimal("160"), Decimal("110"), Decimal("5")),
    RobotType.ROVER: (Decimal("180"), Decimal("120"), Decimal("5")),
    RobotType.ROBOT_ARM: (Decimal("120"), Decimal("120"), Decimal("6")),
    RobotType.BALANCING_BOT: (Decimal("90"), Decimal("70"), Decimal("5")),
    RobotType.DRONE: (Decimal("160"), Decimal("160"), Decimal("4")),
    RobotType.CUSTOM: (Decimal("140"), Decimal("100"), Decimal("5")),
}


def _print_material(value: object) -> PrintMaterial:
    try:
        return PrintMaterial(str(value))
    except ValueError:
        return PrintMaterial.PLA


def _infill_percent(value: object) -> int:
    try:
        return max(0, min(100, int(str(value))))
    except (TypeError, ValueError):
        return 35


def _price_per_gram(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        price = Decimal(str(value))
    except Exception:
        return None
    return price if price >= 0 else None


def _box_stl(length: float, width: float, height: float, name: str) -> str:
    """Return a closed, two-triangle-per-face ASCII STL box."""

    length_mm, width_mm, height_mm = length, width, height
    vertices = {
        "p0": (0.0, 0.0, 0.0),
        "p1": (length_mm, 0.0, 0.0),
        "p2": (length_mm, width_mm, 0.0),
        "p3": (0.0, width_mm, 0.0),
        "p4": (0.0, 0.0, height_mm),
        "p5": (length_mm, 0.0, height_mm),
        "p6": (length_mm, width_mm, height_mm),
        "p7": (0.0, width_mm, height_mm),
    }
    faces = (
        ((0.0, 0.0, -1.0), ("p0", "p3", "p2", "p1")),
        ((0.0, 0.0, 1.0), ("p4", "p5", "p6", "p7")),
        ((0.0, -1.0, 0.0), ("p0", "p1", "p5", "p4")),
        ((0.0, 1.0, 0.0), ("p2", "p3", "p7", "p6")),
        ((-1.0, 0.0, 0.0), ("p3", "p0", "p4", "p7")),
        ((1.0, 0.0, 0.0), ("p1", "p2", "p6", "p5")),
    )
    lines = [f"solid {name}"]
    for normal, corners in faces:
        a, b, c, d = (vertices[corner] for corner in corners)
        for triangle in ((a, b, c), (a, c, d)):
            lines.append(f"  facet normal {normal[0]:.1f} {normal[1]:.1f} {normal[2]:.1f}")
            lines.append("    outer loop")
            for vertex in triangle:
                lines.append(f"      vertex {vertex[0]:.3f} {vertex[1]:.3f} {vertex[2]:.3f}")
            lines.append("    endloop")
            lines.append("  endfacet")
    lines.append(f"endsolid {name}")
    return "\n".join(lines) + "\n"


class MechanicalDesignAgent(BaseAgent):
    """Produces a parametric chassis, STL, weight, and material prices."""

    name = AgentName.MECHANICAL
    display_name = "Mechanical Design"
    description = (
        "Generates a basic parametric chassis STL, estimates printed weight, and "
        "prices it with the JOD material chart."
    )
    depends_on = (AgentName.PLANNER, AgentName.COMPONENT_RESEARCH)
    input_model = MechanicalInput
    output_model = MechanicalOutput
    status = "available"
    milestone = "M7"
    owner_area = "Mechanical Design"

    async def execute(self, request: AgentRequest) -> MechanicalOutput:
        specification = request.context.shared.specification
        if specification is None:
            raise ValueError("Mechanical Design requires a robot specification.")

        default_length, default_width, default_height = _DEFAULT_SIZE[specification.robot_type]
        dimensions = specification.dimensions
        length = Decimal(str(dimensions.length_mm or default_length))
        width = Decimal(str(dimensions.width_mm or default_width))
        thickness = Decimal(str(dimensions.height_mm or default_height))

        volume_mm3 = length * width * thickness
        volume_cm3 = (volume_mm3 / Decimal("1000")).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

        material = _print_material(request.parameters.get("print_material"))
        infill = _infill_percent(request.parameters.get("print_infill_percent"))
        custom_price = _price_per_gram(request.parameters.get("print_price_per_gram_jod"))
        material_fraction = material_fraction_for_infill(infill)
        overrides = {material: custom_price} if custom_price is not None else None
        quotes = [
            PrintMaterialQuote.model_validate(quote)
            for quote in price_print(
                volume_cm3,
                infill_percent=infill,
                material_fraction=material_fraction,
                price_overrides=overrides,
                selected_material=material,
            )
        ]
        cheapest = min(quotes, key=lambda quote: quote.total_jod)
        selected = next(quote for quote in quotes if quote.is_selected)

        filename = f"{request.context.project_name.lower().replace(' ', '-')}-chassis.stl"
        stl = _box_stl(
            float(length),
            float(width),
            float(thickness),
            name=filename.removesuffix(".stl"),
        )

        chassis = MechanicalPart(
            name="Chassis plate",
            category="structure",
            quantity=1,
            material=material.value,
            dimensions_mm=Dimensions(
                length_mm=float(length), width_mm=float(width), height_mm=float(thickness)
            ),
            notes=(
                "Basic rectangular reference plate. Add motor mounts, sensor ears, and "
                "fastener holes before printing the final part."
            ),
        )
        parts = [
            chassis,
            MechanicalPart(
                name="M3 standoff",
                category="fastener",
                quantity=4,
                material="Brass",
                dimensions_mm=Dimensions(length_mm=6, width_mm=6, height_mm=10),
                notes="Raises the electronics plate above the chassis.",
            ),
            MechanicalPart(
                name="M3 x 10 mm screw",
                category="fastener",
                quantity=8,
                material="Steel",
                notes="Four screws for the plate, four for the motors.",
            ),
        ]
        steps = [
            AssemblyStep(
                order=1,
                title="Print and inspect the chassis",
                instructions=(
                    "Print the generated STL at the stated dimensions, remove supports, "
                    "and check that the plate is flat."
                ),
                tools=["3D printer", "deburring tool"],
                parts=["Chassis plate"],
                safety_notes=["Let the bed cool before removing a thin plate."],
            ),
            AssemblyStep(
                order=2,
                title="Fit standoffs and electronics",
                instructions=(
                    "Install the four M3 standoffs, place the controller and driver on "
                    "the plate, and mark any additional mounting holes."
                ),
                tools=["Hex key", "marker", "drill"],
                parts=["M3 standoff", "M3 x 10 mm screw"],
                safety_notes=["Unplug power before drilling or fitting hardware."],
            ),
            AssemblyStep(
                order=3,
                title="Mount the drivetrain",
                instructions=(
                    "Attach the motors and wheels, route wires away from the wheels, and "
                    "spin each wheel by hand before applying power."
                ),
                tools=["Screwdriver", "wire clips"],
                parts=["M3 x 10 mm screw"],
                safety_notes=["Keep fingers clear of the wheels during the first spin test."],
            ),
            AssemblyStep(
                order=4,
                title="Check mass and centre of gravity",
                instructions=(
                    "Weigh the assembled chassis, compare it with the estimate, and move "
                    "the battery to balance the robot before the first drive."
                ),
                tools=["Scale"],
                parts=[],
                safety_notes=["Support the robot so it cannot drive off the bench."],
            ),
        ]

        warnings = [
            "The STL is a reference plate, not a production-ready enclosure.",
            (
                "Weigh the actual print; the estimate uses a "
                f"{material_fraction * 100:.1f}% effective material fraction for "
                f"{infill}% infill."
            ),
        ]
        if custom_price is not None:
            warnings.append(
                f"Your custom {material.value} price of {custom_price} JOD/g replaces the "
                "chart rate for the selected material only."
            )
        if request.parameters.get("custom_pcb"):
            warnings.append(
                "A custom PCB was requested. The chassis still needs mounting holes and "
                "clearance for the final board outline."
            )

        pricing_notes = [
            "PLA: 0.070 JOD/g, base 0.500, minimum 1.000.",
            "PETG: 0.120 JOD/g, base 0.500, minimum 1.200.",
            "ABS: 0.120 JOD/g, base 0.500, minimum 1.000.",
            "Resin: 0.300 JOD/g, base 0.500, minimum 1.500.",
            "TPU: 0.200 JOD/g, base 2.000, minimum 1.200.",
        ]
        if custom_price is not None:
            pricing_notes.append(
                f"Selected {material.value} uses your {custom_price} JOD/g rate; "
                "other materials keep the chart rate."
            )

        return MechanicalOutput(
            chassis=chassis,
            parts=parts,
            assembly_steps=steps,
            drawings=[f"stl:{filename}"],
            manufacturing_notes=[
                "STL units are millimetres.",
                (
                    f"Material weights use the required JOD print chart with a "
                    f"{material_fraction * 100:.1f}% effective material fraction for "
                    f"{infill}% infill."
                ),
                (
                    f"Selected print: {selected.material.value} at "
                    f"{selected.price_per_gram_jod} JOD/g, {selected.weight_g} g, "
                    f"{selected.total_jod} JOD."
                ),
                f"Cheapest estimate: {cheapest.material.value} at {cheapest.total_jod} JOD.",
            ],
            warnings=warnings,
            dimensions_mm=Dimensions(
                length_mm=float(length), width_mm=float(width), height_mm=float(thickness)
            ),
            volume_cm3=volume_cm3,
            infill_percent=infill,
            material_fraction=material_fraction,
            selected_material=material,
            custom_price_per_gram_jod=custom_price,
            print_price_jod=selected.total_jod,
            stl_ascii=stl,
            stl_filename=filename,
            material_quotes=quotes,
            pricing_notes=pricing_notes,
        )


__all__ = ["MechanicalDesignAgent"]
