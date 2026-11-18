"""Project documentation generated from the shared build artifact.

This is not an AI agent: it is a deterministic renderer that keeps docs in sync
with what the pipeline actually produced. Missing stages are stated explicitly
rather than invented.
"""

from __future__ import annotations

from decimal import Decimal

from app.ai.contracts import (
    BuildPreferences,
    ComponentResearchOutput,
    CostEstimate,
    DocumentationFile,
    ElectricalPlan,
    MechanicalOutput,
    ProjectDocumentation,
    RobotIdentification,
    RobotSpecificationDraft,
)


def _money(value: Decimal | float | None) -> str:
    if value is None:
        return "—"
    return f"{Decimal(str(value)):.2f} JOD"


def _bom_table(research: ComponentResearchOutput | None) -> str:
    if research is None:
        return "_No bill of materials was generated._"
    lines = [
        "| Part | Qty | Cheapest store | Price | Other offers |",
        "| --- | ---: | --- | ---: | --- |",
    ]
    for item in research.bill_of_materials:
        selection = item.selection
        if selection is None:
            lines.append(f"| {item.role} | {item.quantity} | unresolved | — | — |")
            continue
        offers = ", ".join(f"{offer.label} {offer.price_jod} JOD" for offer in selection.offers[1:])
        lines.append(
            f"| {selection.name} | {item.quantity} | "
            f"{selection.cheapest_store.value if selection.cheapest_store else '—'} | "
            f"{_money(selection.cheapest_price_jod)} | {offers or '—'} |"
        )
    lines.append("")
    lines.append(f"Estimated component subtotal: **{_money(research.total_estimated_jod)}**.")
    lines.append("")
    lines.append(
        "> Store prices are curated estimates sorted cheapest first. "
        "Confirm stock and price before ordering."
    )
    return "\n".join(lines)


def build_documentation(
    *,
    project_name: str,
    description: str,
    preferences: BuildPreferences | None,
    identification: RobotIdentification | None,
    specification: RobotSpecificationDraft | None,
    research: ComponentResearchOutput | None,
    electrical: ElectricalPlan | None,
    programming: object | None,
    mechanical: MechanicalOutput | None,
    cost: CostEstimate | None,
) -> ProjectDocumentation:
    """Render the full project documentation set."""

    prefs = preferences
    shops = (
        ", ".join(store.value for store in prefs.shops) if prefs and prefs.shops else "all stores"
    )
    languages = (
        ", ".join(language.value for language in prefs.languages)
        if prefs and prefs.languages
        else "Python, C++"
    )
    controllers = ", ".join(prefs.controllers) if prefs and prefs.controllers else "auto-selected"
    pcb = "yes" if prefs and prefs.custom_pcb else "no"

    identified = (
        identification.robot_type.value
        if identification
        else (specification.robot_type.value if specification else "custom")
    )
    overview = f"""# {project_name}

{description}

## Guided decisions

| Decision | Answer |
| --- | --- |
| Identified robot | {identified} |
| Stores | {shops} |
| Languages | {languages} |
| Controllers | {controllers} |
| Custom PCB | {pcb} |
| Platform | {specification.target_platform.value if specification else "undecided"} |
| Print material | cheapest of the required chart |

## What is included

- Sourced component estimates, cheapest store first.
- A validated electrical pinout and schematic exports.
- Multi-file code scaffolds for every selected language.
- A parametric chassis STL, weight estimate, and print price.
- This documentation set.

## Honest limits

- Store prices are estimates, not live supplier quotes.
- Generated code is a scaffold and must be verified on hardware.
- The STL is a reference plate for price and weight, not a production enclosure.
"""
    wiring = f"""# Wiring and electrical plan

{_electrical_summary(electrical)}

{_pinout_table(electrical)}

{_issue_list(electrical)}
"""
    firmware = f"""# Firmware

Selected languages: **{languages}**.

{_programming_summary(programming)}

Every bundle is generated from the validated controller pin map. Complete the
TODO blocks, compile, and verify each pin before applying power.
"""
    mechanical_md = f"""# Mechanical and 3D print price

{_mechanical_summary(mechanical)}
"""
    safety = """# Safety checklist

- Keep the battery unplugged while wiring.
- Check continuity and polarity before the first power-on.
- Use a current-limited supply or the specified fuse.
- Test motors with the wheels raised.
- Keep a physical power disconnect within reach.
- Do not run unattended until the robot has completed a supervised test.
"""
    sourcing = f"""# Sourcing

Stores selected: **{shops}**.

{_bom_table(research)}
"""
    decision_log = f"""# Decision log

- Robot identification: {identification.rationale if identification else "manual selection"}.
- Shops: {shops}.
- Languages: {languages}.
- Controllers: {controllers}.
- Custom PCB: {pcb}.
- Budget: {_money(prefs.budget_max_usd if prefs else None)}.
"""
    files = [
        DocumentationFile(path="README.md", title="Project overview", content=overview),
        DocumentationFile(path="docs/sourcing.md", title="Sourcing and BOM", content=sourcing),
        DocumentationFile(path="docs/wiring.md", title="Wiring", content=wiring),
        DocumentationFile(path="docs/firmware.md", title="Firmware", content=firmware),
        DocumentationFile(
            path="docs/mechanical.md", title="Mechanical and pricing", content=mechanical_md
        ),
        DocumentationFile(path="docs/safety.md", title="Safety", content=safety),
        DocumentationFile(path="docs/decisions.md", title="Decision log", content=decision_log),
    ]
    if cost is not None:
        files.append(
            DocumentationFile(
                path="docs/budget.md",
                title="Budget",
                content=(
                    "# Budget\n\n"
                    f"- Components: {_money(cost.subtotal_jod)}\n"
                    f"- 3D print: {_money(cost.print_cost_jod)}\n"
                    f"- Total: {_money(cost.total_jod)}\n"
                    f"- Budget status: {cost.budget_status}\n\n"
                    + "\n".join(f"- {assumption}" for assumption in cost.assumptions)
                ),
            )
        )
    return ProjectDocumentation(
        files=files,
        summary=(
            "Generated documentation covers sourcing, wiring, firmware, mechanical "
            "pricing, safety, and the guided decisions."
        ),
        notes=["Docs are rebuilt from the latest successful agent artifacts."],
    )


def _electrical_summary(plan: ElectricalPlan | None) -> str:
    if plan is None:
        return "_No electrical plan was generated._"
    return (
        f"- Nodes: {len(plan.nodes)}\n"
        f"- Connections: {len(plan.connections)}\n"
        f"- Nets: {len({connection.net for connection in plan.connections})}\n"
        f"- Validation findings: {len(plan.issues)}\n"
        f"- Peak current: {plan.power_budget.peak_current_ma or 0:.0f} mA\n"
    )


def _pinout_table(plan: ElectricalPlan | None) -> str:
    if plan is None or not plan.pinout:
        return ""
    lines = ["| Ref | Part | Pin | Net | Destinations |", "| --- | --- | --- | --- | --- |"]
    for entry in plan.pinout:
        if not entry.connected:
            continue
        destinations = ", ".join(f"{item.ref}.{item.pin}" for item in entry.destinations) or "—"
        lines.append(
            f"| {entry.ref} | {entry.part} | {entry.pin} | {entry.net or '—'} | {destinations} |"
        )
    return "\n".join(lines)


def _issue_list(plan: ElectricalPlan | None) -> str:
    if plan is None or not plan.issues:
        return "No blocking validation issues were recorded."
    return "\n".join(
        f"- **{issue.severity.upper()}** `{issue.code}`: {issue.message}" for issue in plan.issues
    )


def _programming_summary(programming: object | None) -> str:
    bundles = getattr(programming, "bundles", None)
    if not bundles:
        return "_No code bundle was generated._"
    lines = ["| Language | Framework | Files | Status |", "| --- | --- | ---: | --- |"]
    for bundle in bundles:
        lines.append(
            f"| {bundle.display_name} | {bundle.framework or '—'} | "
            f"{len(bundle.files)} | {bundle.status} |"
        )
    return "\n".join(lines)


def _mechanical_summary(mechanical: MechanicalOutput | None) -> str:
    if mechanical is None:
        return "_No mechanical model was generated._"
    dimensions = mechanical.dimensions_mm
    lines = [
        f"- Model: `{mechanical.stl_filename}`",
        f"- Dimensions: {dimensions.length_mm} x {dimensions.width_mm} x {dimensions.height_mm} mm",
        f"- Volume: {mechanical.volume_cm3} cm³",
        f"- Infill: {mechanical.infill_percent}%",
        "",
        "| Material | JOD/g | Base | Minimum | Weight | Total |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for quote in mechanical.material_quotes:
        marker = " (cheapest)" if quote.is_cheapest else ""
        lines.append(
            f"| {quote.material.value}{marker} | {quote.price_per_gram_jod} | "
            f"{quote.base_jod} | {quote.minimum_jod} | {quote.weight_g} g | {quote.total_jod} JOD |"
        )
    return "\n".join(lines)


__all__ = ["build_documentation"]
