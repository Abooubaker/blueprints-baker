"""Human- and tool-facing exports for an electrical plan.

Formats are deliberately boring and inspectable:

* ``wiring-csv`` — one row per connection, opens in any spreadsheet;
* ``bom-csv`` — the bill of materials for purchasing;
* ``kicad-netlist`` — KiCad S-expression netlist, importable by KiCad and by
  EasyEDA Pro's KiCad importer;
* ``svg`` — a printable wiring overview;
* ``markdown`` — a build guide with pin map, checks, and ordered steps;
* ``json`` — the raw ``ElectricalPlan`` contract.

Nothing in this module calls a network service or an LLM.
"""

from __future__ import annotations

import csv
import html
import io
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from app.ai.contracts import ComponentResearchOutput, ElectricalPlan

ExportFormat = Literal["json", "wiring-csv", "bom-csv", "kicad-netlist", "svg", "markdown"]


@dataclass(frozen=True, slots=True)
class ExportSpec:
    format: ExportFormat
    label: str
    filename: str
    media_type: str
    description: str


EXPORT_SPECS: dict[ExportFormat, ExportSpec] = {
    "wiring-csv": ExportSpec(
        format="wiring-csv",
        label="Wiring table",
        filename="wiring.csv",
        media_type="text/csv; charset=utf-8",
        description="Every net as a spreadsheet row.",
    ),
    "kicad-netlist": ExportSpec(
        format="kicad-netlist",
        label="KiCad / EasyEDA netlist",
        filename="robocraft.net",
        media_type="text/plain; charset=utf-8",
        description="KiCad S-expression netlist for EasyEDA Pro or KiCad import.",
    ),
    "svg": ExportSpec(
        format="svg",
        label="Wiring diagram",
        filename="wiring.svg",
        media_type="image/svg+xml; charset=utf-8",
        description="Printable connection overview with net colors.",
    ),
    "markdown": ExportSpec(
        format="markdown",
        label="Build guide",
        filename="build-guide.md",
        media_type="text/markdown; charset=utf-8",
        description="Pin map, safety checks, and ordered wiring steps.",
    ),
    "bom-csv": ExportSpec(
        format="bom-csv",
        label="Bill of materials",
        filename="bill-of-materials.csv",
        media_type="text/csv; charset=utf-8",
        description="Purchasing list with quantities and prices.",
    ),
    "json": ExportSpec(
        format="json",
        label="JSON plan",
        filename="electrical-plan.json",
        media_type="application/json; charset=utf-8",
        description="The raw typed contract for other tools.",
    ),
}


@dataclass(frozen=True, slots=True)
class ExportArtifact:
    spec: ExportSpec
    content: str


def _csv(rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(rows)
    return buffer.getvalue()


def export_wiring_csv(plan: ElectricalPlan) -> str:
    rows = [
        [
            "net",
            "kind",
            "from_ref",
            "from_pin",
            "to_ref",
            "to_pin",
            "signal",
            "voltage_v",
            "wire_color",
            "wire_gauge_awg",
            "notes",
        ]
    ]
    for connection in plan.connections:
        rows.append(
            [
                connection.net,
                connection.kind,
                connection.from_ref,
                connection.from_pin,
                connection.to_ref,
                connection.to_pin,
                connection.signal,
                "" if connection.voltage_v is None else f"{connection.voltage_v:g}",
                connection.wire_color,
                "" if connection.wire_gauge_awg is None else str(connection.wire_gauge_awg),
                connection.notes,
            ]
        )
    return _csv(rows)


def export_bom_csv(bom: ComponentResearchOutput | None) -> str:
    rows = [
        [
            "role",
            "category",
            "quantity",
            "component",
            "manufacturer",
            "model_number",
            "unit_price_usd",
            "line_total_usd",
            "supplier",
            "rationale",
        ]
    ]
    if bom is not None:
        for item in bom.bill_of_materials:
            selection = item.selection
            unit = selection.price_usd if selection and selection.price_usd is not None else None
            total = unit * item.quantity if unit is not None else None
            rows.append(
                [
                    item.role,
                    item.category,
                    str(item.quantity),
                    selection.name if selection else "unresolved",
                    selection.manufacturer if selection else "",
                    selection.model_number if selection else "",
                    "" if unit is None else f"{unit:.2f}",
                    "" if total is None else f"{total:.2f}",
                    selection.supplier if selection else "",
                    item.rationale,
                ]
            )
    return _csv(rows)


def _sexpr_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def export_kicad_netlist(plan: ElectricalPlan) -> str:
    """Emit a KiCad-style S-expression netlist.

    EasyEDA Pro imports KiCad netlists; KiCad can read the file directly. Pin
    names follow the component library, so a matching schematic symbol is still
    required before a PCB layout is final.
    """

    nets: dict[str, set[tuple[str, str]]] = {}
    for connection in plan.connections:
        nets.setdefault(connection.net, set()).add((connection.from_ref, connection.from_pin))
        nets.setdefault(connection.net, set()).add((connection.to_ref, connection.to_pin))

    def net_order(name: str) -> tuple[int, str]:
        return (0 if name == "GND" else 1 if name == "VBAT" else 2, name)

    lines = [
        '(export (version "E")',
        "  (design",
        '    (source "RoboCraft")',
        f"    (date {_sexpr_string(datetime.now(UTC).date().isoformat())})",
        f'    (tool "RoboCraft electrical engine v{plan.library_version}")',
        "  )",
        "  (components",
    ]
    for node in sorted(plan.nodes, key=lambda item: item.ref):
        tstamp = uuid.uuid5(uuid.NAMESPACE_URL, f"robocraft:{node.ref}")
        lines.extend(
            [
                "    (comp",
                f"      (ref {_sexpr_string(node.ref)})",
                f"      (value {_sexpr_string(node.label)})",
                '      (footprint "")',
                f"      (libsource (lib {_sexpr_string('robocraft')}) "
                f"(part {_sexpr_string(node.library_key or 'unknown')}))",
                f"      (property (name {_sexpr_string('Description')}) "
                f"(value {_sexpr_string(node.role or node.label)}))",
                '      (sheetpath (names "/") (tstamps "/"))',
                f"      (tstamps {_sexpr_string(str(tstamp))})",
                "    )",
            ]
        )
    lines.append("  )")
    lines.append("  (nets")
    for code, name in enumerate(sorted(nets, key=net_order), start=1):
        lines.append("    (net")
        lines.append(f"      (code {_sexpr_string(str(code))})")
        lines.append(f"      (name {_sexpr_string(name)})")
        for ref, pin in sorted(nets[name]):
            lines.append(f"      (node (ref {_sexpr_string(ref)}) (pin {_sexpr_string(pin)}))")
        lines.append("    )")
    lines.append("  )")
    lines.append(")")
    lines.append("")
    return "\n".join(lines)


def _svg_text(
    value: str, x: float, y: float, *, size: int, fill: str, anchor: str = "start"
) -> str:
    return (
        f'<text x="{x:.0f}" y="{y:.0f}" font-family="Menlo, monospace" font-size="{size}" '
        f'fill="{fill}" text-anchor="{anchor}">{html.escape(value)}</text>'
    )


def export_svg(plan: ElectricalPlan) -> str:
    """Render a deterministic, dependency-free wiring overview."""

    column_by_kind = {
        "power": 0,
        "regulator": 1,
        "controller": 2,
        "driver": 3,
        "motor": 4,
        "actuator": 5,
        "sensor": 6,
        "other": 7,
    }
    rows: dict[int, int] = {}
    positions: dict[str, tuple[float, float]] = {}
    nodes = sorted(
        plan.nodes,
        key=lambda node: (column_by_kind.get(node.kind, 7), node.ref),
    )
    for node in nodes:
        column = column_by_kind.get(node.kind, 7)
        row = rows.get(column, 0)
        rows[column] = row + 1
        positions[node.ref] = (40.0 + column * 168.0, 150.0 + row * 108.0)

    max_rows = max(rows.values(), default=1)
    width = 1400
    height = int(210 + max_rows * 108)
    color_by_kind = {
        "power": "#f26d6d",
        "ground": "#5f6e68",
        "signal": "#5cdbd3",
        "motor": "#f5b544",
        "bus": "#8fa9ff",
    }

    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="RoboCraft wiring overview">',
        "<defs>",
        '<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">',
        '<path d="M 24 0 L 0 0 0 24" fill="none" stroke="#152023" stroke-width="1"/>',
        "</pattern>",
        "</defs>",
        f'<rect width="{width}" height="{height}" fill="#06090a"/>',
        f'<rect width="{width}" height="{height}" fill="url(#grid)"/>',
        _svg_text("ROBOCRAFT · WIRING OVERVIEW", 40, 52, size=18, fill="#edf2ee"),
        _svg_text(
            f"{len(plan.nodes)} parts · {len({c.net for c in plan.connections})} nets · "
            f"{plan.power_budget.peak_current_ma or 0:.0f} mA peak",
            40,
            78,
            size=11,
            fill="#94a29c",
        ),
    ]

    for connection in plan.connections:
        start = positions.get(connection.from_ref)
        end = positions.get(connection.to_ref)
        if start is None or end is None:
            continue
        x1, y1 = start[0] + 62, start[1] + 22
        x2, y2 = end[0] + 62, end[1] + 22
        midx = (x1 + x2) / 2
        color = color_by_kind.get(connection.kind, "#94a29c")
        opacity = "0.18" if connection.kind == "ground" else "0.55"
        parts.append(
            f'<path d="M {x1:.0f} {y1:.0f} C {midx:.0f} {y1:.0f}, {midx:.0f} {y2:.0f}, '
            f'{x2:.0f} {y2:.0f}" fill="none" stroke="{color}" stroke-width="1.4" '
            f'opacity="{opacity}"><title>{html.escape(connection.net)}: '
            f"{html.escape(connection.from_ref)}.{html.escape(connection.from_pin)} → "
            f"{html.escape(connection.to_ref)}.{html.escape(connection.to_pin)}</title></path>"
        )

    fill_by_kind = {
        "power": "#1b1113",
        "regulator": "#101a1a",
        "controller": "#141c0d",
        "driver": "#101a1a",
        "motor": "#1b1810",
        "actuator": "#1b1810",
        "sensor": "#0f1a1c",
        "other": "#10171a",
    }
    for node in nodes:
        x, y = positions[node.ref]
        fill = fill_by_kind.get(node.kind, "#10171a")
        parts.append(
            f"<g><title>{html.escape(node.label)} · {html.escape(node.ref)}</title>"
            f'<rect x="{x:.0f}" y="{y:.0f}" width="150" height="58" rx="8" '
            f'fill="{fill}" stroke="#223034"/>'
            f'<text x="{x + 10:.0f}" y="{y + 20:.0f}" font-family="Menlo, monospace" '
            f'font-size="11" fill="#c9f75a">{html.escape(node.ref)}</text>'
            f'<text x="{x + 10:.0f}" y="{y + 38:.0f}" font-family="Inter, sans-serif" '
            f'font-size="10" fill="#edf2ee">{html.escape(node.label[:26])}</text>'
            f'<text x="{x + 10:.0f}" y="{y + 51:.0f}" font-family="Menlo, monospace" '
            f'font-size="8" fill="#5f6e68">{html.escape(node.kind.upper())}</text></g>'
        )

    legend = [
        ("power", "Power"),
        ("ground", "Ground"),
        ("signal", "Signal"),
        ("motor", "Motor"),
        ("bus", "Bus"),
    ]
    for index, (kind, label) in enumerate(legend):
        x = 40 + index * 110
        y = height - 42
        parts.append(
            f'<line x1="{x}" y1="{y - 4}" x2="{x + 18}" y2="{y - 4}" '
            f'stroke="{color_by_kind[kind]}" stroke-width="2"/>'
        )
        parts.append(_svg_text(label, x + 24, y, size=10, fill="#94a29c"))
    parts.append(
        _svg_text(
            f"LIBRARY v{plan.library_version} · CHECK ALL CONNECTIONS BEFORE POWER-ON",
            width - 40,
            height - 20,
            size=9,
            fill="#5f6e68",
            anchor="end",
        )
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def export_markdown(plan: ElectricalPlan, bom: ComponentResearchOutput | None, title: str) -> str:
    lines = [
        f"# {title} — wiring guide",
        "",
        "Generated by the RoboCraft deterministic electrical engine. "
        "Verify every connection against the component datasheet before power-on.",
        "",
        "## Power budget",
        "",
        f"- Supply: {plan.power_budget.supply_voltage_v or 'unknown'} V",
        f"- Peak load: {plan.power_budget.peak_current_ma or 0:.0f} mA",
        f"- Typical load: {plan.power_budget.typical_current_ma or 0:.0f} mA",
        f"- Recommended supply: {plan.power_budget.recommended_supply_ma or 0:.0f} mA",
        f"- Estimated runtime: {plan.power_budget.estimated_runtime_min or 0:.0f} min",
        "",
        "## Parts",
        "",
        "| Ref | Part | Role | Logic / supply |",
        "| --- | --- | --- | --- |",
    ]
    for node in plan.nodes:
        supply = f"{node.voltage_v:g} V" if node.voltage_v is not None else "—"
        lines.append(f"| {_md(node.ref)} | {_md(node.label)} | {_md(node.role)} | {_md(supply)} |")

    lines.extend(["", "## Pin map", "", "| Pin | Signal |", "| --- | --- |"])
    for pin, signal in sorted(plan.pin_map.items()):
        lines.append(f"| {_md(pin)} | {_md(signal)} |")

    lines.extend(["", "## Nets", "", "| Net | From | To | Signal |", "| --- | --- | --- | --- |"])
    for connection in plan.connections:
        lines.append(
            f"| {_md(connection.net)} | {_md(connection.from_ref)}.{_md(connection.from_pin)} "
            f"| {_md(connection.to_ref)}.{_md(connection.to_pin)} | {_md(connection.signal)} |"
        )

    lines.extend(["", "## Safety checks", ""])
    lines.extend(f"- PASS — {check}" for check in plan.safety_checks)
    for issue in plan.issues:
        lines.append(f"- {issue.severity.upper()} — {issue.message}")
        if issue.remediation:
            lines.append(f"  - Fix: {issue.remediation}")

    lines.extend(["", "## Wiring order", ""])
    for index, step in enumerate(plan.wiring_steps, start=1):
        lines.append(f"{index}. {step}")

    if bom is not None and bom.unresolved_requirements:
        lines.extend(["", "## Open requirements", ""])
        lines.extend(f"- {item}" for item in bom.unresolved_requirements)

    lines.append("")
    return "\n".join(lines)


def export_artifact(
    fmt: ExportFormat,
    plan: ElectricalPlan,
    bom: ComponentResearchOutput | None,
    *,
    project_name: str,
) -> ExportArtifact:
    spec = EXPORT_SPECS[fmt]
    if fmt == "wiring-csv":
        content = export_wiring_csv(plan)
    elif fmt == "bom-csv":
        content = export_bom_csv(bom)
    elif fmt == "kicad-netlist":
        content = export_kicad_netlist(plan)
    elif fmt == "svg":
        content = export_svg(plan)
    elif fmt == "markdown":
        content = export_markdown(plan, bom, project_name)
    else:
        content = plan.model_dump_json(indent=2) + "\n"
    return ExportArtifact(spec=spec, content=content)


__all__ = [
    "EXPORT_SPECS",
    "ExportArtifact",
    "ExportFormat",
    "ExportSpec",
    "export_artifact",
    "export_bom_csv",
    "export_kicad_netlist",
    "export_markdown",
    "export_svg",
    "export_wiring_csv",
]
