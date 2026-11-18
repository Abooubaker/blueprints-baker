# Electrical & wiring system

Albayraq turns an approved bill of materials into a deterministic wiring plan: every
component gets a reference designator, every physical pin is allocated, nets are named,
the power tree is budgeted, and safety rules are checked before the plan is returned.

No language model is involved in this stage. The planner and component research agents
are deterministic too, so the same specification always produces the same plan.

## What the plan contains

`ElectricalPlan` (in `apps/api/app/ai/contracts.py`) is the single typed contract used by
the API, the web workspace, and every exporter:

| Field | Meaning |
| --- | --- |
| `nodes` | Every part with reference designator, role, voltage, current, and pins |
| `connections` | Point-to-point wiring with net name, signal, kind, wire color, and gauge |
| `pinout` | One row per physical pin, including spare pins and every exact destination |
| `pin_map` | Controller pin → net assignment |
| `power_budget` | Pack voltage, peak/typical current, recommended supply, runtime |
| `power_rails` | Named rails (`GND`, `VBAT`, `5V_CTRL`, `3V3_CTRL`, `DRIVER_LOGIC`, regulator output) |
| `issues` | Validation findings with severity, affected refs, and remediation |
| `safety_checks` | Checks that passed (grounding, pin conflicts, current headroom, …) |
| `wiring_steps` | Ordered assembly instructions that respect power-down first |
| `design_notes` | Constraints and caveats worth surfacing in the guide |

Connection kinds are `power`, `ground`, `signal`, `motor`, and `bus`. Issue severities are
`error` (blocking), `warning` (review), and `info` (note).

## Component library

The curated library lives in `apps/api/app/electrical/library.py`. Each profile records:

- category, role, manufacturer, model, and planning price;
- supply range, logic voltage, typical and peak current;
- physical pins (name, electrical kind, voltage);
- interfaces (`gpio`, `pwm`, `i2c`, `analog`, `uart`, …);
- notes used in the BOM and build guide.

Reference designs define the required roles per robot archetype (line follower, obstacle
avoider, rover, robot arm, balancing bot, drone). A controller is selected from the target
platform, then `build_reference_bom` resolves each role to a library part.

Adding a part means adding a `ComponentProfile`; the engine picks it up automatically when
a reference design or compatibility rule selects it.

## Validation rules

The engine reports issues instead of silently guessing:

- **`motor_overvoltage`** — motor nominal voltage is below the pack/rail voltage. The plan
  stays usable, but the issue tells you to add a buck converter or pick a different motor.
- **`logic_level_mismatch`** — a 5 V output drives a 3.3 V input (for example an HC-SR04
  echo pin into an ESP32). A warning with the divider/level-shifter remediation.
- **`pin_conflict`** — two nets claim the same controller pin (blocking).
- **`missing_ground`** — a powered part has no ground path (blocking).
- **`current_over_budget`** — peak load exceeds the recommended supply margin.
- **`battery_missing`** / **`controller_missing`** — the design cannot be wired.

Passed checks are returned separately so the UI can show both what was verified and what
needs review.

## API

All routes are under `/api/v1/projects/{project_id}/electrical`.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/` | Run planner → component research → electrical and persist the artifact. Returns `201`. |
| `GET` | `/` | Return the latest persisted artifact. `404` when no plan exists. |
| `GET` | `/export/{format}` | Download an export as an attachment. |

Formats: `json`, `wiring-csv`, `pinout-csv`, `bom-csv`, `kicad-netlist`, `kicad-schematic`,
`svg`, `markdown`.

```bash
curl -X POST http://localhost:8000/api/v1/projects/$PROJECT_ID/electrical
curl -OJ http://localhost:8000/api/v1/projects/$PROJECT_ID/electrical/export/kicad-netlist
```

The artifact stores the `agent_run_id` so the plan can be traced to the audit record.

## Exports and EasyEDA

| Format | File | Use |
| --- | --- | --- |
| `json` | `electrical-plan.json` | Raw contract for other tools and tests |
| `wiring-csv` | `wiring.csv` | Spreadsheet review of every net |
| `pinout-csv` | `pinout.csv` | Every physical pin with its net, signal, and exact destination(s) |
| `bom-csv` | `bill-of-materials.csv` | Purchasing list with quantities and prices |
| `kicad-netlist` | `albayraq.net` | KiCad S-expression netlist |
| `kicad-schematic` | `albayraq.kicad_sch` | Self-contained KiCad schematic, one labelled wire per pin |
| `svg` | `wiring.svg` | Blueprint-style pin-level schematic with destinations |
| `markdown` | `build-guide.md` | Full pinout, safety checks, ordered wiring steps |

**EasyEDA:** the `.net` file is a KiCad S-expression netlist and the `.kicad_sch` file is a
KiCad 8 schematic with embedded library symbols. EasyEDA Pro can import both KiCad formats;
KiCad opens them natively. The export is deliberately honest about what it is — Albayraq
does not emit an undocumented EasyEDA-native JSON format, and imported symbols must be
reviewed before layout. Every physical pin in the schematic has a short wire and a global
label, so unconnected pins explicitly appear as `NC_<ref>_<pin>` instead of disappearing.
The generators are covered by structural tests (balanced S-expressions, a symbol and wire per
pin, a label per net), not by an automated KiCad/EasyEDA round-trip; run ERC after import.

## Engine layers

```text
app/electrical/library.py    curated profiles, reference BOMs, controller selection
app/electrical/engine.py     pin allocation, net naming, wiring, power budget, validation
app/electrical/exporters.py  CSV / KiCad netlist + schematic / SVG / Markdown / JSON
app/services/electrical_service.py  orchestrates agents and persists the artifact
app/api/v1/endpoints/electrical.py  HTTP surface
```

`apps/web/src/components/projects/wiring-workspace.tsx` renders the same contract:
a pin-level schematic where every row names its pin and destination, a searchable full pinout
(including spare pins), a filterable net table, a power/rails panel, severity-grouped
validation, wiring steps, and one consolidated export menu.

## Limits

- The library is finite and deliberately curated; unknown parts do not get invented pins.
- Prices are planning estimates, not live supplier quotes.
- The netlist and schematic are structural (symbols, nets, pins), not a routed PCB layout.
- Symbol geometry is generated for readability; verify footprints and symbol pin mappings
  against the manufacturer datasheet before manufacturing.
- The engine validates declared electrical limits; it does not simulate the circuit.
