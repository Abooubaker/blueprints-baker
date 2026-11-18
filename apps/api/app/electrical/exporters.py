"""Human- and tool-facing exports for an electrical plan.

Formats are deliberately boring and inspectable:

* ``wiring-csv`` — one row per connection, opens in any spreadsheet;
* ``pinout-csv`` — one row per physical pin with its exact destination(s);
* ``bom-csv`` — the bill of materials for purchasing;
* ``kicad-netlist`` — KiCad S-expression netlist, importable by KiCad and by
  EasyEDA Pro's KiCad importer;
* ``kicad-schematic`` — a self-contained KiCad schematic with one embedded
  symbol per part and a labelled wire on every physical pin;
* ``svg`` — a printable pin-level wiring schematic;
* ``markdown`` — a build guide with the full pinout, checks, and ordered steps;
* ``json`` — the raw ``ElectricalPlan`` contract.

Nothing in this module calls a network service or an LLM.
"""

from __future__ import annotations

import csv
import html
import io
import uuid
from dataclasses import dataclass
from typing import Literal

from app.ai.contracts import (
    ComponentResearchOutput,
    ElectricalNode,
    ElectricalPlan,
)

ExportFormat = Literal[
    "json",
    "wiring-csv",
    "pinout-csv",
    "bom-csv",
    "kicad-netlist",
    "kicad-schematic",
    "svg",
    "markdown",
]


@dataclass(frozen=True, slots=True)
class ExportSpec:
    format: ExportFormat
    label: str
    filename: str
    media_type: str
    description: str


EXPORT_SPECS: dict[ExportFormat, ExportSpec] = {
    "kicad-schematic": ExportSpec(
        format="kicad-schematic",
        label="KiCad schematic",
        filename="albayraq.kicad_sch",
        media_type="text/plain; charset=utf-8",
        description="Self-contained KiCad schematic, one labelled wire per pin.",
    ),
    "kicad-netlist": ExportSpec(
        format="kicad-netlist",
        label="KiCad / EasyEDA netlist",
        filename="albayraq.net",
        media_type="text/plain; charset=utf-8",
        description="KiCad S-expression netlist for EasyEDA Pro or KiCad import.",
    ),
    "pinout-csv": ExportSpec(
        format="pinout-csv",
        label="Full pinout",
        filename="pinout.csv",
        media_type="text/csv; charset=utf-8",
        description="Every physical pin with its exact destination and wire.",
    ),
    "wiring-csv": ExportSpec(
        format="wiring-csv",
        label="Wiring table",
        filename="wiring.csv",
        media_type="text/csv; charset=utf-8",
        description="Every net as a spreadsheet row.",
    ),
    "svg": ExportSpec(
        format="svg",
        label="Pin-level schematic",
        filename="wiring.svg",
        media_type="image/svg+xml; charset=utf-8",
        description="Blueprint-style schematic with every pin and destination.",
    ),
    "markdown": ExportSpec(
        format="markdown",
        label="Build guide",
        filename="build-guide.md",
        media_type="text/markdown; charset=utf-8",
        description="Full pinout, safety checks, and ordered wiring steps.",
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


def export_pinout_csv(plan: ElectricalPlan) -> str:
    rows = [
        [
            "ref",
            "part",
            "role",
            "pin",
            "pin_kind",
            "pin_voltage_v",
            "net",
            "signal",
            "connected",
            "destination_count",
            "destinations",
            "wire_color",
            "wire_gauge_awg",
        ]
    ]
    for entry in plan.pinout:
        destinations = "; ".join(
            f"{destination.ref}.{destination.pin}" for destination in entry.destinations
        )
        rows.append(
            [
                entry.ref,
                entry.part,
                entry.role,
                entry.pin,
                entry.pin_kind,
                "" if entry.voltage_v is None else f"{entry.voltage_v:g}",
                entry.net,
                entry.signal,
                "yes" if entry.connected else "no",
                str(len(entry.destinations)),
                destinations,
                entry.wire_color,
                "" if entry.wire_gauge_awg is None else str(entry.wire_gauge_awg),
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
        '    (source "Albayraq")',
        f'    (tool "Albayraq electrical engine v{plan.library_version}")',
        "  )",
        "  (components",
    ]
    for node in sorted(plan.nodes, key=lambda item: item.ref):
        tstamp = uuid.uuid5(uuid.NAMESPACE_URL, f"albayraq:{node.ref}")
        lines.extend(
            [
                "    (comp",
                f"      (ref {_sexpr_string(node.ref)})",
                f"      (value {_sexpr_string(node.label)})",
                '      (footprint "")',
                f"      (libsource (lib {_sexpr_string('albayraq')}) "
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


def _kicad_id(seed: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"albayraq:{seed}"))


def _kicad_net(value: str, *, fallback: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in "_+-./" else "_" for character in value
    ).strip("_")
    return cleaned or fallback


def export_kicad_schematic(plan: ElectricalPlan, *, project_name: str) -> str:
    """Emit a self-contained KiCad schematic with a labelled wire on every pin.

    Symbols are generated from the Albayraq library, so the file does not
    depend on an external symbol table. Nets are connected by global labels,
    which is also what makes the file readable by EasyEDA Pro's KiCad importer.
    Structural validity is covered by tests; always open the file in KiCad or
    EasyEDA Pro and run ERC before manufacturing.
    """

    kind_column = {
        "power": 0,
        "regulator": 1,
        "controller": 2,
        "driver": 3,
        "motor": 4,
        "actuator": 5,
        "sensor": 6,
        "other": 7,
    }
    column_cursor: dict[int, float] = {}
    origin: dict[str, tuple[float, float]] = {}
    for node in sorted(plan.nodes, key=lambda item: (kind_column.get(item.kind, 7), item.ref)):
        column = kind_column.get(node.kind, 7)
        height = 17.78 + max(1, len(node.pins)) * 2.54
        top = column_cursor.get(column, 25.4)
        origin[node.ref] = (25.4 + column * 55.88, top)
        column_cursor[column] = top + height + 12.7

    root_uuid = _kicad_id(f"schematic:{project_name}")
    lines: list[str] = [
        "(kicad_sch",
        "  (version 20231120)",
        '  (generator "eeschema")',
        '  (generator_version "8.0")',
        f'  (uuid "{root_uuid}")',
        '  (paper "A3")',
        "  (title_block",
        f"    (title {_sexpr_string(f'{project_name} — Albayraq wiring')})",
        '    (rev "1")',
        "    (comment 1 "
        f"{_sexpr_string('Generated by the Albayraq deterministic electrical engine')})",
        "  )",
        "  (lib_symbols",
    ]

    for node in plan.nodes:
        symbol_ref = f"albayraq:{node.ref}"
        bottom = -(12.7 + max(1, len(node.pins) - 1) * 2.54)
        lines.extend(
            [
                f"    (symbol {_sexpr_string(symbol_ref)}",
                "      (pin_names (offset 0.508))",
                "      (exclude_from_sim no)",
                "      (in_bom yes)",
                "      (on_board yes)",
                f'      (property "Reference" {_sexpr_string("U")} (at 0 0 0) '
                "(effects (font (size 1.27 1.27))))",
                f'      (property "Value" {_sexpr_string(node.label)} (at 0 -2.54 0) '
                "(effects (font (size 1.27 1.27))))",
                '      (property "Footprint" "" (at 0 0 0) '
                "(effects (font (size 1.27 1.27)) (hide yes)))",
                '      (property "Datasheet" "" (at 0 0 0) '
                "(effects (font (size 1.27 1.27)) (hide yes)))",
                f"      (symbol {_sexpr_string(f'{node.ref}_0_1')}",
                "        (rectangle (start -12.7 2.54) "
                f"(end 12.7 {bottom:.2f}) "
                "(stroke (width 0.254) (type default)) (fill (type background)))",
                "      )",
                f"      (symbol {_sexpr_string(f'{node.ref}_1_1')}",
            ]
        )
        for index, pin in enumerate(node.pins, start=1):
            relative_y = -(10.16 + (index - 1) * 2.54)
            lines.extend(
                [
                    f"        (pin passive line (at 17.78 {relative_y:.2f} 180) (length 5.08)",
                    f"          (name {_sexpr_string(pin.name)} "
                    "(effects (font (size 1.016 1.016))))",
                    f"          (number {_sexpr_string(str(index))} "
                    "(effects (font (size 1.016 1.016))))",
                    "        )",
                ]
            )
        lines.extend(["      )", "    )"])

    lines.append("  )")

    for node in plan.nodes:
        origin_x, origin_y = origin[node.ref]
        lines.extend(
            [
                "  (symbol",
                f"    (lib_id {_sexpr_string(f'albayraq:{node.ref}')})",
                f"    (lib_name {_sexpr_string(f'albayraq:{node.ref}')})",
                f"    (at {origin_x:.2f} {origin_y:.2f} 0)",
                "    (unit 1)",
                "    (exclude_from_sim no)",
                "    (in_bom yes)",
                "    (on_board yes)",
                "    (dnp no)",
                f'    (uuid "{_kicad_id(f"symbol:{node.ref}")}")',
                f'    (property "Reference" {_sexpr_string(node.ref)} '
                f"(at {origin_x:.2f} {origin_y - 3.81:.2f} 0) "
                "(effects (font (size 1.27 1.27))))",
                f'    (property "Value" {_sexpr_string(node.label)} '
                f"(at {origin_x:.2f} {origin_y - 1.27:.2f} 0) "
                "(effects (font (size 1.27 1.27))))",
                f'    (property "Footprint" "" (at {origin_x:.2f} {origin_y:.2f} 0) '
                "(effects (font (size 1.27 1.27)) (hide yes)))",
                f'    (property "Datasheet" "" (at {origin_x:.2f} {origin_y:.2f} 0) '
                "(effects (font (size 1.27 1.27)) (hide yes)))",
                f'    (property "Description" {_sexpr_string(node.role or node.label)} '
                f"(at {origin_x:.2f} {origin_y:.2f} 0) "
                "(effects (font (size 1.27 1.27)) (hide yes)))",
            ]
        )
        for index, _pin in enumerate(node.pins, start=1):
            lines.append(
                f"    (pin {_sexpr_string(str(index))} "
                f'(uuid "{_kicad_id(f"pin:{node.ref}:{index}")}"))'
            )
        lines.extend(
            [
                "    (instances",
                f"      (project {_sexpr_string('albayraq')}",
                f"        (path {_sexpr_string(f'/{root_uuid}')} "
                f"(reference {_sexpr_string(node.ref)}) (unit 1))",
                "      )",
                "    )",
                "  )",
            ]
        )

    pinout_by_pin = {(entry.ref, entry.pin): entry for entry in plan.pinout}
    for node in plan.nodes:
        origin_x, origin_y = origin[node.ref]
        for index, pin in enumerate(node.pins, start=1):
            pin_y = origin_y + 10.16 + (index - 1) * 2.54
            wire_start = origin_x + 17.78
            wire_end = origin_x + 22.86
            entry = pinout_by_pin.get((node.ref, pin.name))
            net_name = _kicad_net(
                entry.net if entry and entry.net else "", fallback=f"NC_{node.ref}_{pin.name}"
            )
            lines.extend(
                [
                    "  (wire",
                    f"    (pts (xy {wire_start:.2f} {pin_y:.2f}) (xy {wire_end:.2f} {pin_y:.2f}))",
                    "    (stroke (width 0) (type default))",
                    f'    (uuid "{_kicad_id(f"wire:{node.ref}:{pin.name}")}")',
                    "  )",
                    f"  (global_label {_sexpr_string(net_name)}",
                    "    (shape passive)",
                    f"    (at {wire_end:.2f} {pin_y:.2f} 0)",
                    "    (effects (font (size 1.016 1.016)) (justify left))",
                    f'    (uuid "{_kicad_id(f"label:{node.ref}:{pin.name}")}")',
                    "  )",
                ]
            )

    lines.extend(
        [
            '  (sheet_instances (path "/" (page "1")))',
            ")",
            "",
        ]
    )
    return "\n".join(lines)


def _svg_text(
    value: str, x: float, y: float, *, size: int, fill: str, anchor: str = "start"
) -> str:
    return (
        f'<text x="{x:.0f}" y="{y:.0f}" font-family="Menlo, monospace" font-size="{size}" '
        f'fill="{fill}" text-anchor="{anchor}">{html.escape(value)}</text>'
    )


def export_svg(plan: ElectricalPlan) -> str:
    """Render a deterministic, dependency-free pin-level wiring schematic."""

    kind_column = {
        "power": 0,
        "regulator": 1,
        "controller": 2,
        "driver": 3,
        "motor": 4,
        "actuator": 5,
        "sensor": 6,
        "other": 7,
    }
    used_columns = sorted({kind_column.get(node.kind, 7) for node in plan.nodes})
    column_slot = {column: index for index, column in enumerate(used_columns)}

    node_width = 268
    row_height = 15
    header_height = 37
    nodes_by_column: dict[int, list[ElectricalNode]] = {}
    for node in sorted(plan.nodes, key=lambda item: (kind_column.get(item.kind, 7), item.ref)):
        column = kind_column.get(node.kind, 7)
        nodes_by_column.setdefault(column, []).append(node)

    positions: dict[str, tuple[float, float, float]] = {}
    for column, column_nodes in nodes_by_column.items():
        y = 112.0
        for node in column_nodes:
            height = header_height + max(1, len(node.pins)) * row_height + 10
            positions[node.ref] = (40.0 + column_slot[column] * 292.0, y, height)
            y += height + 18.0

    max_bottom = max((value[1] + value[2] for value in positions.values()), default=320.0)
    width = 80 + len(used_columns) * 292
    height = int(max(420.0, max_bottom + 96))
    color_by_kind = {
        "power": "#ff9b9b",
        "ground": "#7fa8c8",
        "signal": "#6fd6ff",
        "motor": "#ffcc7a",
        "bus": "#eaf6ff",
    }

    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Albayraq pin-level wiring schematic">',
        "<defs>",
        '<pattern id="bp-minor" width="24" height="24" patternUnits="userSpaceOnUse">',
        '<path d="M 24 0 L 0 0 0 24" fill="none" stroke="#ffffff" stroke-opacity="0.05" '
        'stroke-width="1"/>',
        "</pattern>",
        '<pattern id="bp-major" width="120" height="120" patternUnits="userSpaceOnUse">',
        '<rect width="120" height="120" fill="url(#bp-minor)"/>',
        '<path d="M 120 0 L 0 0 0 120" fill="none" stroke="#ffffff" stroke-opacity="0.1" '
        'stroke-width="1"/>',
        "</pattern>",
        "</defs>",
        f'<rect width="{width}" height="{height}" fill="#07233d"/>',
        f'<rect width="{width}" height="{height}" fill="url(#bp-major)"/>',
        _svg_text(
            "ALBAYRAQ · PIN-LEVEL WIRING SCHEMATIC",
            40,
            52,
            size=18,
            fill="#f2f8ff",
        ),
        _svg_text(
            f"{len(plan.nodes)} parts · {len(plan.pinout)} physical pins · "
            f"{len({c.net for c in plan.connections})} nets · "
            f"{plan.power_budget.peak_current_ma or 0:.0f} mA peak",
            40,
            78,
            size=11,
            fill="#b9d4ea",
        ),
        _svg_text(
            "Every pin row names its exact destination. Labels mark unconnected pins.",
            width - 40,
            78,
            size=10,
            fill="#7fa8c8",
            anchor="end",
        ),
    ]

    destination_by_pin: dict[tuple[str, str], str] = {}
    for entry in plan.pinout:
        if entry.destinations:
            destination_by_pin[(entry.ref, entry.pin)] = ", ".join(
                f"{destination.ref}.{destination.pin}" for destination in entry.destinations
            )
        else:
            destination_by_pin[(entry.ref, entry.pin)] = "not connected"

    pin_index = {
        (node.ref, pin.name): index for node in plan.nodes for index, pin in enumerate(node.pins)
    }

    # Faint routing behind the part blocks keeps the pin rows readable.
    for connection in plan.connections:
        source = positions.get(connection.from_ref)
        target = positions.get(connection.to_ref)
        if source is None or target is None:
            continue
        sx, sy, _ = source
        tx, ty, _ = target
        source_entry = pin_index.get((connection.from_ref, connection.from_pin))
        target_entry = pin_index.get((connection.to_ref, connection.to_pin))
        if source_entry is None or target_entry is None:
            continue
        y1 = sy + header_height + source_entry * row_height + 7
        y2 = ty + header_height + target_entry * row_height + 7
        x1 = sx + node_width
        x2 = tx + node_width
        mid = max(x1, x2) + 16
        color = color_by_kind.get(connection.kind, "#b9d4ea")
        parts.append(
            f'<path d="M {x1:.0f} {y1:.0f} H {mid:.0f} V {y2:.0f} H {x2:.0f}" '
            f'fill="none" stroke="{color}" stroke-width="1.1" stroke-opacity="0.34" '
            f'stroke-linejoin="round"><title>{html.escape(connection.net)}: '
            f"{html.escape(connection.from_ref)}.{html.escape(connection.from_pin)} → "
            f"{html.escape(connection.to_ref)}.{html.escape(connection.to_pin)}</title></path>"
        )

    for node in plan.nodes:
        x, y, block_height = positions[node.ref]
        parts.append(
            f"<g><title>{html.escape(node.label)} · {html.escape(node.ref)}</title>"
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{node_width}" height="{block_height:.0f}" '
            'rx="4" fill="#0b2f4f" fill-opacity="0.94" stroke="#eaf6ff" '
            'stroke-opacity="0.55" stroke-width="1.1"/>'
            f'<line x1="{x:.0f}" y1="{y + header_height:.0f}" x2="{x + node_width:.0f}" '
            f'y2="{y + header_height:.0f}" stroke="#eaf6ff" stroke-opacity="0.28"/>'
            f'<text x="{x + 10:.0f}" y="{y + 17:.0f}" font-family="Menlo, monospace" '
            f'font-size="11" fill="#eaf6ff">{html.escape(node.ref)}</text>'
            f'<text x="{x + 44:.0f}" y="{y + 17:.0f}" font-family="Inter, sans-serif" '
            f'font-size="10" fill="#f2f8ff">{html.escape(node.label[:28])}</text>'
            f'<text x="{x + 10:.0f}" y="{y + 30:.0f}" font-family="Menlo, monospace" '
            f'font-size="7" fill="#7fa8c8">{html.escape(node.kind.upper())} · '
            f"{len(node.pins)} PINS</text>"
            f'<text x="{x + node_width - 10:.0f}" y="{y + 30:.0f}" '
            'font-family="Menlo, monospace" font-size="7" fill="#7fa8c8" '
            'text-anchor="end">PIN → DESTINATION</text>'
        )
        for index, pin in enumerate(node.pins):
            row_y = y + header_height + index * row_height
            destination = destination_by_pin.get((node.ref, pin.name), "not connected")
            connected = destination != "not connected"
            if len(destination) > 34:
                destination = destination[:33] + "…"
            parts.append(
                f'<text x="{x + 10:.0f}" y="{row_y + 11:.0f}" '
                f'font-family="Menlo, monospace" font-size="8.5" '
                f'fill="{"#f2f8ff" if connected else "#7fa8c8"}">'
                f"{html.escape(pin.name[:16])}</text>"
                f'<text x="{x + node_width - 10:.0f}" y="{row_y + 11:.0f}" '
                'font-family="Menlo, monospace" font-size="8" text-anchor="end" '
                f'fill="{"#6fd6ff" if connected else "#7fa8c8"}">'
                f"{html.escape(destination)}</text>"
                f'<circle cx="{x + node_width:.0f}" cy="{row_y + 7:.0f}" r="1.6" '
                f'fill="{"#6fd6ff" if connected else "#2d6894"}"/>'
            )
        parts.append("</g>")

    legend = [
        ("power", "Power"),
        ("ground", "Ground"),
        ("signal", "Signal"),
        ("motor", "Motor"),
        ("bus", "Bus"),
    ]
    for index, (kind, label) in enumerate(legend):
        x = 40 + index * 110
        y = height - 40
        parts.append(
            f'<line x1="{x}" y1="{y - 4}" x2="{x + 18}" y2="{y - 4}" '
            f'stroke="{color_by_kind[kind]}" stroke-width="2"/>'
        )
        parts.append(_svg_text(label, x + 24, y, size=10, fill="#b9d4ea"))
    parts.append(
        _svg_text(
            f"LIBRARY v{plan.library_version} · CHECK ALL CONNECTIONS BEFORE POWER-ON",
            width - 40,
            height - 20,
            size=9,
            fill="#7fa8c8",
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
        "Generated by the Albayraq deterministic electrical engine. "
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

    lines.extend(
        [
            "",
            "## Full pinout",
            "",
            "| Ref | Part | Pin | Net | Signal | Destination | Wire |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for entry in plan.pinout:
        destinations = (
            ", ".join(f"{destination.ref}.{destination.pin}" for destination in entry.destinations)
            or "not connected"
        )
        wire = (
            f"{entry.wire_color} · {entry.wire_gauge_awg} AWG"
            if entry.wire_color or entry.wire_gauge_awg
            else "—"
        )
        lines.append(
            f"| {_md(entry.ref)} | {_md(entry.part)} | {_md(entry.pin)} "
            f"| {_md(entry.net or '—')} | {_md(entry.signal or '—')} "
            f"| {_md(destinations)} | {_md(wire)} |"
        )

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
    elif fmt == "pinout-csv":
        content = export_pinout_csv(plan)
    elif fmt == "bom-csv":
        content = export_bom_csv(bom)
    elif fmt == "kicad-netlist":
        content = export_kicad_netlist(plan)
    elif fmt == "kicad-schematic":
        content = export_kicad_schematic(plan, project_name=project_name)
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
    "export_kicad_schematic",
    "export_markdown",
    "export_pinout_csv",
    "export_svg",
    "export_wiring_csv",
]
