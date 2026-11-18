"use client";

import {
  AlertTriangle,
  ArrowLeft,
  BatteryCharging,
  Cable,
  CheckCircle2,
  CircuitBoard,
  Cpu,
  Download,
  FileJson,
  Gauge,
  Info,
  Loader2,
  PlugZap,
  RefreshCw,
  Search,
  ShieldCheck,
  Table2,
  Waypoints,
  XCircle,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/form";
import { EmptyState, Separator } from "@/components/ui/misc";
import { api, ApiError } from "@/lib/api";
import { DEMO_MODE } from "@/lib/constants";
import type {
  ConnectionKind,
  ElectricalArtifact,
  ElectricalNode,
  ElectricalPlan,
  ExportFormat,
  IssueSeverity,
} from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

type TabKey = "diagram" | "connections" | "pins" | "power" | "validation" | "steps";

const TABS: { key: TabKey; label: string; icon: typeof CircuitBoard }[] = [
  { key: "diagram", label: "Diagram", icon: Waypoints },
  { key: "connections", label: "Connections", icon: Table2 },
  { key: "pins", label: "Pin map", icon: Cpu },
  { key: "power", label: "Power", icon: BatteryCharging },
  { key: "validation", label: "Validation", icon: ShieldCheck },
  { key: "steps", label: "Build order", icon: Cable },
];

const KIND_STYLES: Record<ConnectionKind, { label: string; chip: string; stroke: string }> = {
  power: {
    label: "Power",
    chip: "border-danger/25 bg-danger/10 text-danger",
    stroke: "#f26d6d",
  },
  ground: {
    label: "Ground",
    chip: "border-line bg-elevated text-muted",
    stroke: "#5f6e68",
  },
  signal: {
    label: "Signal",
    chip: "border-aqua/25 bg-aqua/10 text-aqua",
    stroke: "#5cdbd3",
  },
  motor: {
    label: "Motor",
    chip: "border-warn/25 bg-warn/10 text-warn",
    stroke: "#f5b544",
  },
  bus: {
    label: "Bus",
    chip: "border-signal/25 bg-signal/10 text-signal",
    stroke: "#c9f75a",
  },
};

const NODE_ORDER: ElectricalNode["kind"][] = [
  "power",
  "regulator",
  "controller",
  "driver",
  "motor",
  "actuator",
  "sensor",
  "other",
];

const NODE_STYLE: Record<ElectricalNode["kind"], { stroke: string; fill: string }> = {
  power: { stroke: "rgba(242,109,109,0.55)", fill: "rgba(242,109,109,0.07)" },
  regulator: { stroke: "rgba(245,181,68,0.55)", fill: "rgba(245,181,68,0.06)" },
  controller: { stroke: "rgba(201,247,90,0.55)", fill: "rgba(201,247,90,0.06)" },
  driver: { stroke: "rgba(92,219,211,0.55)", fill: "rgba(92,219,211,0.06)" },
  motor: { stroke: "rgba(245,181,68,0.45)", fill: "rgba(245,181,68,0.05)" },
  actuator: { stroke: "rgba(245,181,68,0.35)", fill: "rgba(245,181,68,0.04)" },
  sensor: { stroke: "rgba(92,219,211,0.35)", fill: "rgba(92,219,211,0.04)" },
  other: { stroke: "rgba(95,110,104,0.7)", fill: "rgba(24,35,38,0.9)" },
};

const SEVERITY: Record<
  IssueSeverity,
  { label: string; icon: typeof AlertTriangle; className: string; badge: string }
> = {
  error: {
    label: "Blocking",
    icon: XCircle,
    className: "border-danger/25 bg-danger/[0.05]",
    badge: "danger",
  },
  warning: {
    label: "Review",
    icon: AlertTriangle,
    className: "border-warn/25 bg-warn/[0.05]",
    badge: "warn",
  },
  info: {
    label: "Note",
    icon: Info,
    className: "border-aqua/25 bg-aqua/[0.05]",
    badge: "aqua",
  },
};

function volts(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : `${value} V`;
}

function milliamps(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value >= 1000 ? `${(value / 1000).toFixed(2)} A` : `${value.toFixed(0)} mA`;
}

function nodeLayout(plan: ElectricalPlan) {
  const rows = new Map<number, number>();
  const positions = new Map<string, { x: number; y: number; column: number }>();
  for (const node of plan.nodes) {
    const column = Math.max(0, NODE_ORDER.indexOf(node.kind));
    const row = rows.get(column) ?? 0;
    rows.set(column, row + 1);
    positions.set(node.ref, { x: 20 + column * 196, y: 28 + row * 96, column });
  }
  const maxRows = Math.max(1, ...rows.values());
  return {
    positions,
    width: 20 + NODE_ORDER.length * 196,
    height: 28 + maxRows * 96,
  };
}

function Diagram({
  plan,
  selectedNode,
  selectedNet,
  onSelectNode,
  onSelectNet,
}: {
  plan: ElectricalPlan;
  selectedNode: string | null;
  selectedNet: string | null;
  onSelectNode: (ref: string | null) => void;
  onSelectNet: (net: string | null) => void;
}) {
  const { positions, width, height } = useMemo(() => nodeLayout(plan), [plan]);
  const matchingConnections = useMemo(
    () =>
      plan.connections.filter(
        (connection) =>
          (!selectedNode ||
            connection.from_ref === selectedNode ||
            connection.to_ref === selectedNode) &&
          (!selectedNet || connection.net === selectedNet),
      ),
    [plan.connections, selectedNode, selectedNet],
  );
  const activeRefs = new Set(
    matchingConnections.flatMap((connection) => [connection.from_ref, connection.to_ref]),
  );

  return (
    <div className="border-line-soft bg-canvas/60 overflow-x-auto rounded-xl border">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="min-w-[760px]"
        role="img"
        aria-label="Interactive wiring diagram"
      >
        <defs>
          <pattern id="wiring-grid" width="24" height="24" patternUnits="userSpaceOnUse">
            <path d="M 24 0 L 0 0 0 24" fill="none" stroke="#182326" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width={width} height={height} fill="url(#wiring-grid)" />

        {plan.connections.map((connection, index) => {
          const from = positions.get(connection.from_ref);
          const to = positions.get(connection.to_ref);
          if (!from || !to) return null;
          const active =
            matchingConnections.includes(connection) &&
            (selectedNode !== null || selectedNet !== null);
          const x1 = from.x + 78;
          const y1 = from.y + 29;
          const x2 = to.x + 78;
          const y2 = to.y + 29;
          const middle = (x1 + x2) / 2;
          return (
            <path
              key={`${connection.net}-${connection.from_ref}-${connection.from_pin}-${index}`}
              d={`M ${x1} ${y1} C ${middle} ${y1}, ${middle} ${y2}, ${x2} ${y2}`}
              fill="none"
              stroke={KIND_STYLES[connection.kind].stroke}
              strokeWidth={active ? 2.4 : 1.2}
              strokeOpacity={selectedNet === connection.net ? 0.95 : active ? 0.7 : 0.2}
              className="cursor-pointer transition-all"
              onClick={() => onSelectNet(connection.net)}
            >
              <title>
                {connection.net}: {connection.from_ref}.{connection.from_pin} → {connection.to_ref}.
                {connection.to_pin}
              </title>
            </path>
          );
        })}

        {plan.nodes.map((node) => {
          const position = positions.get(node.ref);
          if (!position) return null;
          const dimmed =
            (selectedNode !== null || selectedNet !== null) && !activeRefs.has(node.ref);
          return (
            <g
              key={node.ref}
              transform={`translate(${position.x} ${position.y})`}
              opacity={dimmed ? 0.38 : 1}
              className="cursor-pointer transition-opacity"
              onClick={() => onSelectNode(selectedNode === node.ref ? null : node.ref)}
            >
              <title>
                {node.label} · {node.ref}
              </title>
              <rect
                width={156}
                height={58}
                rx={10}
                strokeWidth={1.2}
                stroke={NODE_STYLE[node.kind].stroke}
                fill={NODE_STYLE[node.kind].fill}
              />
              <text
                x={11}
                y={21}
                fontFamily="JetBrains Mono, monospace"
                fontSize={11}
                fill="#c9f75a"
              >
                {node.ref}
              </text>
              <text x={11} y={38} fontFamily="Inter, sans-serif" fontSize={10} fill="#edf2ee">
                {node.label.length > 25 ? `${node.label.slice(0, 24)}…` : node.label}
              </text>
              <text
                x={11}
                y={51}
                fontFamily="JetBrains Mono, monospace"
                fontSize={7.5}
                fill="#5f6e68"
              >
                {node.kind.toUpperCase()} · {node.pins.filter((pin) => pin.connected).length} PIN
                {node.pins.filter((pin) => pin.connected).length === 1 ? "" : "S"}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="border-line-soft flex flex-wrap items-center gap-3 border-t px-4 py-2.5">
        <span className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">Legend</span>
        {(Object.keys(KIND_STYLES) as ConnectionKind[]).map((kind) => (
          <span key={kind} className="text-faint flex items-center gap-1.5 text-[10px]">
            <span className="h-px w-4" style={{ backgroundColor: KIND_STYLES[kind].stroke }} />
            {KIND_STYLES[kind].label}
          </span>
        ))}
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: string;
  hint: string;
  icon: typeof Gauge;
}) {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">{label}</p>
        <Icon className="text-faint size-3.5" />
      </div>
      <p className="text-ink mt-2.5 text-xl font-medium tracking-tight">{value}</p>
      <p className="text-faint mt-1 text-[10px]">{hint}</p>
    </Card>
  );
}

function PinMap({ plan }: { plan: ElectricalPlan }) {
  const controllers = plan.nodes.filter((node) => node.kind === "controller");
  const [controllerRef, setControllerRef] = useState(controllers[0]?.ref ?? "");
  const controller = controllers.find((node) => node.ref === controllerRef) ?? controllers[0];

  if (!controller) {
    return <p className="text-faint text-xs">No controller is present in this plan.</p>;
  }

  const pinMap = plan.pin_map;

  return (
    <div className="space-y-4">
      {controllers.length > 1 ? (
        <div className="flex flex-wrap gap-1.5">
          {controllers.map((item) => (
            <Button
              key={item.ref}
              size="sm"
              variant={item.ref === controller.ref ? "secondary" : "ghost"}
              onClick={() => setControllerRef(item.ref)}
            >
              {item.ref} · {item.label}
            </Button>
          ))}
        </div>
      ) : null}
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
        {controller.pins.map((pin) => {
          const signal = pinMap[pin.name];
          return (
            <div
              key={pin.name}
              className={cn(
                "rounded-lg border px-3 py-2.5",
                pin.connected ? "border-line bg-elevated/50" : "border-line-soft bg-canvas/30",
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-ink font-mono text-[11px]">{pin.name}</span>
                <Badge variant={pin.connected ? "aqua" : "outline"}>
                  {pin.connected ? "wired" : "free"}
                </Badge>
              </div>
              <p className="text-faint mt-1 truncate text-[10px]" title={signal ?? pin.kind}>
                {signal ?? pin.kind.replace("_", " ")}
              </p>
            </div>
          );
        })}
      </div>
      <p className="text-faint text-[10px] leading-relaxed">
        {plan.safety_checks.find((check) => check.includes("pin")) ??
          "Every assigned pin belongs to exactly one net."}
      </p>
    </div>
  );
}

function PowerPanel({ artifact }: { artifact: ElectricalArtifact }) {
  const { plan, bom } = artifact;
  const budget = plan.power_budget;
  const railRows = plan.power_rails;
  return (
    <div className="space-y-4">
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { label: "Pack", value: volts(budget.supply_voltage_v), icon: BatteryCharging },
          { label: "Peak load", value: milliamps(budget.peak_current_ma), icon: Zap },
          { label: "Supply size", value: milliamps(budget.recommended_supply_ma), icon: PlugZap },
          {
            label: "Est. runtime",
            value:
              budget.estimated_runtime_min === null
                ? "—"
                : `${budget.estimated_runtime_min.toFixed(0)} min`,
            icon: Gauge,
          },
        ].map((item) => (
          <div key={item.label} className="border-line-soft bg-canvas/40 rounded-lg border p-3">
            <div className="text-faint flex items-center justify-between">
              <span className="font-mono text-[8px] tracking-[0.14em] uppercase">{item.label}</span>
              <item.icon className="size-3.5" />
            </div>
            <p className="text-ink mt-2 text-lg font-medium">{item.value}</p>
          </div>
        ))}
      </div>

      <div className="border-line-soft overflow-x-auto rounded-lg border">
        <table className="w-full text-left text-xs">
          <thead className="text-faint bg-elevated/40 font-mono text-[8px] tracking-[0.14em] uppercase">
            <tr>
              <th className="px-3 py-2">Rail</th>
              <th className="px-3 py-2">Voltage</th>
              <th className="px-3 py-2">Peak</th>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">Notes</th>
            </tr>
          </thead>
          <tbody>
            {railRows.map((rail) => (
              <tr key={rail.name} className="border-line-soft border-t">
                <td className="text-signal px-3 py-2 font-mono text-[10px]">{rail.name}</td>
                <td className="text-muted px-3 py-2">{volts(rail.voltage_v)}</td>
                <td className="text-muted px-3 py-2">{milliamps(rail.peak_current_ma)}</td>
                <td className="text-muted px-3 py-2 font-mono text-[10px]">
                  {rail.source_ref || "—"}
                </td>
                <td className="text-faint max-w-[280px] px-3 py-2 text-[10px] leading-relaxed">
                  {rail.notes}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="border-line-soft bg-canvas/40 rounded-lg border p-4">
          <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
            Current headroom
          </p>
          <p className="text-ink mt-2 text-2xl font-medium">
            {budget.margin_percent === null ? "—" : `${budget.margin_percent.toFixed(0)}%`}
          </p>
          <p className="text-faint mt-1 text-[10px]">
            Above the 30% design margin means there is room for stall current.
          </p>
        </div>
        <div className="border-line-soft bg-canvas/40 rounded-lg border p-4">
          <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
            Bill of materials
          </p>
          <p className="text-ink mt-2 text-2xl font-medium">
            {artifact.total_estimated_usd === null
              ? "—"
              : `$${artifact.total_estimated_usd.toFixed(2)}`}
          </p>
          <p className="text-faint mt-1 text-[10px]">
            {bom?.bill_of_materials.length ?? 0} lines · planning estimates, not live quotes.
          </p>
        </div>
      </div>

      {bom ? (
        <div className="border-line-soft overflow-x-auto rounded-lg border">
          <table className="w-full text-left text-xs">
            <thead className="text-faint bg-elevated/40 font-mono text-[8px] tracking-[0.14em] uppercase">
              <tr>
                <th className="px-3 py-2">Role</th>
                <th className="px-3 py-2">Component</th>
                <th className="px-3 py-2">Qty</th>
                <th className="px-3 py-2">Unit</th>
              </tr>
            </thead>
            <tbody>
              {bom.bill_of_materials.map((item, index) => (
                <tr key={`${item.role}-${index}`} className="border-line-soft border-t">
                  <td className="text-faint px-3 py-2 font-mono text-[9px] uppercase">
                    {item.role}
                  </td>
                  <td className="text-muted px-3 py-2">{item.selection?.name ?? "Unresolved"}</td>
                  <td className="text-muted px-3 py-2">{item.quantity}</td>
                  <td className="text-muted px-3 py-2 font-mono text-[10px]">
                    {item.selection?.price_usd === null || item.selection?.price_usd === undefined
                      ? "—"
                      : `$${Number(item.selection.price_usd).toFixed(2)}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}

function ValidationPanel({ plan }: { plan: ElectricalPlan }) {
  const errors = plan.issues.filter((issue) => issue.severity === "error");
  const warnings = plan.issues.filter((issue) => issue.severity === "warning");
  const notes = plan.issues.filter((issue) => issue.severity === "info");

  return (
    <div className="space-y-4">
      <div className="grid gap-2 sm:grid-cols-3">
        {[
          { label: "Blocking", value: errors.length, tone: "text-danger" },
          { label: "Review", value: warnings.length, tone: "text-warn" },
          { label: "Passed checks", value: plan.safety_checks.length, tone: "text-signal" },
        ].map((item) => (
          <div key={item.label} className="border-line-soft bg-canvas/40 rounded-lg border p-3">
            <p className="text-faint font-mono text-[8px] tracking-[0.14em] uppercase">
              {item.label}
            </p>
            <p className={cn("mt-2 text-xl font-medium", item.tone)}>{item.value}</p>
          </div>
        ))}
      </div>

      {plan.issues.length ? (
        <div className="space-y-2">
          {[...errors, ...warnings, ...notes].map((issue, index) => {
            const style = SEVERITY[issue.severity];
            const Icon = style.icon;
            return (
              <div
                key={`${issue.code}-${index}`}
                className={cn("rounded-lg border px-3.5 py-3", style.className)}
              >
                <div className="flex items-start gap-2.5">
                  <Icon
                    className={cn(
                      "mt-0.5 size-4 shrink-0",
                      issue.severity === "error"
                        ? "text-danger"
                        : issue.severity === "warning"
                          ? "text-warn"
                          : "text-aqua",
                    )}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant={style.badge as "danger" | "warn" | "aqua"}>
                        {style.label}
                      </Badge>
                      <span className="text-faint font-mono text-[9px]">{issue.code}</span>
                      {issue.refs.length ? (
                        <span className="text-faint font-mono text-[9px]">
                          {issue.refs.join(" · ")}
                        </span>
                      ) : null}
                    </div>
                    <p className="text-ink mt-1.5 text-xs leading-relaxed">{issue.message}</p>
                    {issue.remediation ? (
                      <p className="text-muted mt-1 text-[11px] leading-relaxed">
                        Fix: {issue.remediation}
                      </p>
                    ) : null}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="border-signal/20 bg-signal/[0.04] flex items-center gap-2.5 rounded-lg border px-4 py-3 text-xs">
          <CheckCircle2 className="text-signal size-4" />
          <span className="text-ink">
            No blocking issues. Review the passed checks before applying power.
          </span>
        </div>
      )}

      <div>
        <p className="text-faint mb-2 font-mono text-[9px] tracking-[0.16em] uppercase">
          Passed checks
        </p>
        <ul className="space-y-1.5">
          {plan.safety_checks.map((check, index) => (
            <li key={index} className="text-muted flex items-start gap-2 text-[11px]">
              <CheckCircle2 className="text-signal/70 mt-0.5 size-3.5 shrink-0" />
              <span className="leading-relaxed">{check}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function StepsPanel({ plan }: { plan: ElectricalPlan }) {
  return (
    <div className="space-y-5">
      <ol className="space-y-2.5">
        {plan.wiring_steps.map((step, index) => (
          <li key={index} className="flex items-start gap-3">
            <span className="border-signal/25 bg-signal/10 text-signal flex size-6 shrink-0 items-center justify-center rounded-full border font-mono text-[10px]">
              {index + 1}
            </span>
            <p className="text-muted pt-0.5 text-xs leading-relaxed">{step}</p>
          </li>
        ))}
      </ol>
      {plan.design_notes.length ? (
        <div className="border-line-soft bg-canvas/40 rounded-lg border p-4">
          <p className="text-faint mb-2 font-mono text-[9px] tracking-[0.16em] uppercase">
            Design notes
          </p>
          <ul className="space-y-1.5">
            {plan.design_notes.map((note, index) => (
              <li key={index} className="text-muted flex items-start gap-2 text-[11px]">
                <span className="bg-aqua/70 mt-1.5 size-1 shrink-0 rounded-full" />
                <span className="leading-relaxed">{note}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export function WiringWorkspace({ projectId }: { projectId: string }) {
  const [artifact, setArtifact] = useState<ElectricalArtifact | null>(null);
  const [loading, setLoading] = useState(true);
  const [missing, setMissing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("diagram");
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [selectedNet, setSelectedNet] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [kindFilter, setKindFilter] = useState<ConnectionKind | "all">("all");

  useEffect(() => {
    let cancelled = false;
    api
      .getElectrical(projectId)
      .then((loaded) => {
        if (cancelled) return;
        setArtifact(loaded);
        setMissing(false);
        setError(null);
      })
      .catch((caught: unknown) => {
        if (cancelled) return;
        if (caught instanceof ApiError && caught.status === 404) {
          setMissing(true);
          setError(null);
        } else {
          setError(
            caught instanceof ApiError
              ? caught.message
              : "Could not load the wiring plan for this project.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const plan = artifact?.plan ?? null;

  const connectionCounts = useMemo(() => {
    const counts = new Map<ConnectionKind, number>();
    for (const connection of plan?.connections ?? []) {
      counts.set(connection.kind, (counts.get(connection.kind) ?? 0) + 1);
    }
    return counts;
  }, [plan]);

  const filteredConnections = useMemo(() => {
    if (!plan) return [];
    const query = search.trim().toLowerCase();
    return plan.connections.filter((connection) => {
      if (kindFilter !== "all" && connection.kind !== kindFilter) return false;
      if (selectedNet && connection.net !== selectedNet) return false;
      if (
        selectedNode &&
        connection.from_ref !== selectedNode &&
        connection.to_ref !== selectedNode
      ) {
        return false;
      }
      if (!query) return true;
      return [
        connection.net,
        connection.signal,
        connection.from_ref,
        connection.from_pin,
        connection.to_ref,
        connection.to_pin,
      ]
        .join(" ")
        .toLowerCase()
        .includes(query);
    });
  }, [plan, kindFilter, search, selectedNet, selectedNode]);

  const issueCounts = useMemo(
    () => ({
      errors: plan?.issues.filter((issue) => issue.severity === "error").length ?? 0,
      warnings: plan?.issues.filter((issue) => issue.severity === "warning").length ?? 0,
    }),
    [plan],
  );

  const selectedNodeInfo = plan?.nodes.find((node) => node.ref === selectedNode) ?? null;

  async function generate() {
    setGenerating(true);
    setError(null);
    try {
      const generated = await api.generateElectrical(projectId);
      setArtifact(generated);
      setMissing(false);
      setSelectedNet(null);
      setSelectedNode(null);
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : "The wiring plan could not be generated.",
      );
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-raised h-4 w-40 animate-pulse rounded" />
        <div className="rounded-panel bg-raised h-28 animate-pulse" />
        <div className="grid gap-3 sm:grid-cols-4">
          {[0, 1, 2, 3].map((item) => (
            <div key={item} className="rounded-panel bg-raised h-24 animate-pulse" />
          ))}
        </div>
        <div className="rounded-panel bg-raised h-[420px] animate-pulse" />
      </div>
    );
  }

  return (
    <div>
      <Link
        href={`/projects/${projectId}`}
        className="text-faint hover:text-ink mb-5 inline-flex items-center gap-1.5 text-xs transition-colors"
      >
        <ArrowLeft className="size-3.5" /> Back to project
      </Link>

      <div className="mb-6 flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Badge variant="aqua">M5 · Wiring</Badge>
            {DEMO_MODE ? <Badge variant="outline">Static demo</Badge> : null}
            {plan ? <Badge variant="outline">library v{plan.library_version}</Badge> : null}
            {artifact ? (
              <span className="text-faint font-mono text-[10px]">
                generated {formatDate(artifact.generated_at)}
              </span>
            ) : null}
          </div>
          <h1 className="text-ink text-[26px] leading-tight font-medium tracking-[-0.02em] sm:text-[30px]">
            Wiring &amp; power
          </h1>
          <p className="text-muted mt-1.5 max-w-2xl text-sm leading-relaxed">
            Pin allocation, nets, power budget, and deterministic safety checks generated from the
            approved bill of materials. Nothing here is guessed by a language model.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {DEMO_MODE ? (
            <span className="border-line bg-elevated/60 text-faint inline-flex h-8 items-center gap-1.5 rounded-lg border px-2.5 font-mono text-[10px]">
              <CircuitBoard className="size-3" /> Precomputed plan
            </span>
          ) : (
            <Button variant="secondary" onClick={() => void generate()} disabled={generating}>
              {generating ? (
                <Loader2 className="size-4 animate-spin" />
              ) : plan ? (
                <RefreshCw className="size-3.5" />
              ) : (
                <CircuitBoard className="size-4" />
              )}
              {plan ? "Regenerate" : "Generate wiring"}
            </Button>
          )}
          {plan && artifact ? (
            <div className="flex flex-wrap gap-1.5">
              {artifact.export_formats
                .filter((format) => format.format !== "json")
                .map((format) => (
                  <a
                    key={format.format}
                    href={api.exportUrl(projectId, format.format as ExportFormat)}
                    download={format.filename}
                    className="border-line bg-elevated text-muted hover:border-signal/35 hover:text-ink inline-flex h-8 items-center gap-1.5 rounded-lg border px-2.5 text-[11px] transition-colors"
                    title={format.description}
                  >
                    <Download className="size-3" />
                    {format.format === "kicad-netlist" ? "Netlist" : format.label}
                  </a>
                ))}
            </div>
          ) : null}
        </div>
      </div>

      {error ? (
        <div className="rounded-panel border-danger/25 bg-danger/[0.05] mb-5 flex items-start gap-2.5 border px-4 py-3">
          <AlertTriangle className="text-danger mt-0.5 size-4 shrink-0" />
          <div className="text-xs">
            <p className="text-ink font-medium">Wiring plan unavailable</p>
            <p className="text-muted mt-1 leading-relaxed">{error}</p>
          </div>
        </div>
      ) : null}

      {missing && !plan ? (
        <EmptyState
          icon={<CircuitBoard className="size-4" />}
          title="No wiring plan yet"
          description="Generate the deterministic plan to allocate pins, build nets, validate voltage and current limits, and unlock EasyEDA/KiCad netlist downloads."
          action={
            <Button onClick={() => void generate()} disabled={generating}>
              {generating ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <CircuitBoard className="size-4" />
              )}
              Generate wiring plan
            </Button>
          }
        />
      ) : null}

      {plan && artifact ? (
        <div className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <Stat
              label="Parts"
              value={String(plan.nodes.length)}
              hint={`${plan.nodes.reduce((sum, node) => sum + node.pins.length, 0)} physical pins modelled`}
              icon={Cpu}
            />
            <Stat
              label="Nets"
              value={String(new Set(plan.connections.map((connection) => connection.net)).size)}
              hint={`${plan.connections.length} point-to-point connections`}
              icon={Cable}
            />
            <Stat
              label="Peak load"
              value={milliamps(plan.power_budget.peak_current_ma)}
              hint={`${milliamps(plan.power_budget.recommended_supply_ma)} recommended supply`}
              icon={Zap}
            />
            <Stat
              label="Findings"
              value={issueCounts.errors ? `${issueCounts.errors} blocking` : "Ready to wire"}
              hint={`${issueCounts.warnings} review item${issueCounts.warnings === 1 ? "" : "s"} · ${plan.safety_checks.length} checks passed`}
              icon={issueCounts.errors ? AlertTriangle : ShieldCheck}
            />
          </div>

          <div className="border-line-soft bg-surface/70 sticky top-16 z-10 -mx-1 overflow-x-auto rounded-xl border p-1 backdrop-blur">
            <div className="flex min-w-max gap-1">
              {TABS.map((tab) => {
                const active = activeTab === tab.key;
                return (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => setActiveTab(tab.key)}
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-[11px] transition-colors",
                      active
                        ? "bg-elevated text-ink shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset]"
                        : "text-faint hover:text-muted hover:bg-white/[0.03]",
                    )}
                  >
                    <tab.icon className={cn("size-3.5", active && "text-signal")} />
                    {tab.label}
                    {tab.key === "validation" && plan.issues.length ? (
                      <span className="bg-warn/15 text-warn rounded-full px-1.5 font-mono text-[8px]">
                        {plan.issues.length}
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          </div>

          {activeTab === "diagram" ? (
            <div className="space-y-3">
              <div className="grid gap-3 xl:grid-cols-[1fr_280px]">
                <Diagram
                  plan={plan}
                  selectedNode={selectedNode}
                  selectedNet={selectedNet}
                  onSelectNode={(ref) => {
                    setSelectedNode(ref);
                    setSelectedNet(null);
                  }}
                  onSelectNet={(net) => {
                    setSelectedNet(net);
                    setSelectedNode(null);
                  }}
                />
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-sm">
                      <Gauge className="text-signal/80 size-4" />
                      {selectedNodeInfo ? `${selectedNodeInfo.ref} inspector` : "Net inspector"}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-xs">
                    {selectedNodeInfo ? (
                      <>
                        <div>
                          <p className="text-ink text-[13px] font-medium">
                            {selectedNodeInfo.label}
                          </p>
                          <p className="text-faint mt-0.5 font-mono text-[9px] uppercase">
                            {selectedNodeInfo.kind} · {selectedNodeInfo.role}
                          </p>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <div className="border-line-soft bg-canvas/40 rounded-md border p-2">
                            <p className="text-faint font-mono text-[8px] uppercase">Rail</p>
                            <p className="text-ink mt-1">{volts(selectedNodeInfo.voltage_v)}</p>
                          </div>
                          <div className="border-line-soft bg-canvas/40 rounded-md border p-2">
                            <p className="text-faint font-mono text-[8px] uppercase">Peak</p>
                            <p className="text-ink mt-1">
                              {milliamps(selectedNodeInfo.peak_current_ma)}
                            </p>
                          </div>
                        </div>
                        <Separator />
                        <div>
                          <p className="text-faint mb-1.5 font-mono text-[8px] uppercase">Pins</p>
                          <div className="flex flex-wrap gap-1">
                            {selectedNodeInfo.pins.map((pin) => (
                              <span
                                key={pin.name}
                                className={cn(
                                  "rounded border px-1.5 py-0.5 font-mono text-[9px]",
                                  pin.connected
                                    ? "border-aqua/25 bg-aqua/10 text-aqua"
                                    : "border-line text-faint",
                                )}
                              >
                                {pin.name}
                              </span>
                            ))}
                          </div>
                        </div>
                        {selectedNodeInfo.notes ? (
                          <p className="text-faint text-[10px] leading-relaxed">
                            {selectedNodeInfo.notes}
                          </p>
                        ) : null}
                      </>
                    ) : selectedNet ? (
                      <>
                        <p className="text-signal font-mono text-[11px]">{selectedNet}</p>
                        <p className="text-faint text-[10px]">
                          {filteredConnections.length} connection
                          {filteredConnections.length === 1 ? "" : "s"} on this net.
                        </p>
                        <div className="space-y-1.5">
                          {plan.connections
                            .filter((connection) => connection.net === selectedNet)
                            .map((connection, index) => (
                              <div
                                key={index}
                                className="border-line-soft bg-canvas/40 rounded-md border px-2 py-1.5 font-mono text-[9px]"
                              >
                                <p className="text-muted">
                                  {connection.from_ref}.{connection.from_pin}
                                </p>
                                <p className="text-faint">
                                  → {connection.to_ref}.{connection.to_pin}
                                </p>
                              </div>
                            ))}
                        </div>
                      </>
                    ) : (
                      <div className="text-faint space-y-2 text-[11px] leading-relaxed">
                        <p>Click a part or a wire in the diagram to focus it.</p>
                        <p>
                          Node colours group power, control, drive, and sensing stages. Hover a wire
                          to see its net.
                        </p>
                        <div className="border-line-soft bg-canvas/40 rounded-md border p-2.5">
                          <p className="text-muted font-mono text-[9px] uppercase">Rules</p>
                          <ul className="mt-1.5 space-y-1">
                            <li>One physical pin per net.</li>
                            <li>Grounds meet at the pack negative.</li>
                            <li>3.3 V inputs never see 5 V logic.</li>
                          </ul>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
              <p className="text-faint text-[10px]">
                The SVG export is print-ready. The KiCad S-expression netlist imports into KiCad and
                EasyEDA Pro; always re-check symbols before layout.
              </p>
            </div>
          ) : null}

          {activeTab === "connections" ? (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <div className="relative">
                  <Search className="text-faint absolute top-1/2 left-3 size-3.5 -translate-y-1/2" />
                  <Input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search nets, pins, signals…"
                    className="h-9 w-[250px] pl-8 text-xs"
                    aria-label="Search connections"
                  />
                </div>
                <div className="flex flex-wrap gap-1">
                  <button
                    type="button"
                    onClick={() => setKindFilter("all")}
                    className={cn(
                      "rounded-full border px-2.5 py-1 font-mono text-[9px] uppercase transition-colors",
                      kindFilter === "all"
                        ? "border-signal/30 bg-signal/10 text-signal"
                        : "border-line text-faint hover:text-muted",
                    )}
                  >
                    All {plan.connections.length}
                  </button>
                  {(Object.keys(KIND_STYLES) as ConnectionKind[])
                    .filter((kind) => connectionCounts.get(kind))
                    .map((kind) => (
                      <button
                        key={kind}
                        type="button"
                        onClick={() => setKindFilter(kind)}
                        className={cn(
                          "rounded-full border px-2.5 py-1 font-mono text-[9px] uppercase transition-colors",
                          kindFilter === kind
                            ? KIND_STYLES[kind].chip
                            : "border-line text-faint hover:text-muted",
                        )}
                      >
                        {KIND_STYLES[kind].label} {connectionCounts.get(kind)}
                      </button>
                    ))}
                </div>
                {selectedNode || selectedNet ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedNode(null);
                      setSelectedNet(null);
                    }}
                  >
                    Clear focus
                  </Button>
                ) : null}
              </div>

              <div className="border-line-soft overflow-x-auto rounded-xl border">
                <table className="w-full min-w-[860px] text-left text-xs">
                  <thead className="text-faint bg-elevated/40 font-mono text-[8px] tracking-[0.14em] uppercase">
                    <tr>
                      <th className="px-3 py-2.5">Net</th>
                      <th className="px-3 py-2.5">Kind</th>
                      <th className="px-3 py-2.5">From</th>
                      <th className="px-3 py-2.5">To</th>
                      <th className="px-3 py-2.5">Signal</th>
                      <th className="px-3 py-2.5">Wire</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredConnections.map((connection, index) => (
                      <tr
                        key={`${connection.net}-${index}`}
                        className={cn(
                          "border-line-soft hover:bg-elevated/30 cursor-pointer border-t transition-colors",
                          selectedNet === connection.net && "bg-elevated/40",
                        )}
                        onClick={() =>
                          setSelectedNet(selectedNet === connection.net ? null : connection.net)
                        }
                      >
                        <td className="text-signal px-3 py-2 font-mono text-[10px]">
                          {connection.net}
                        </td>
                        <td className="px-3 py-2">
                          <span
                            className={cn(
                              "rounded-full border px-1.5 py-0.5 font-mono text-[8px] uppercase",
                              KIND_STYLES[connection.kind].chip,
                            )}
                          >
                            {KIND_STYLES[connection.kind].label}
                          </span>
                        </td>
                        <td className="text-muted px-3 py-2 font-mono text-[10px]">
                          {connection.from_ref}.{connection.from_pin}
                        </td>
                        <td className="text-muted px-3 py-2 font-mono text-[10px]">
                          {connection.to_ref}.{connection.to_pin}
                        </td>
                        <td className="text-faint px-3 py-2 text-[11px]">{connection.signal}</td>
                        <td className="text-faint px-3 py-2 text-[10px]">
                          {connection.wire_color || "—"} · {connection.wire_gauge_awg ?? "—"} AWG
                        </td>
                      </tr>
                    ))}
                    {filteredConnections.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="text-faint px-3 py-8 text-center text-[11px]">
                          No connections match this filter.
                        </td>
                      </tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

          {activeTab === "pins" ? <PinMap plan={plan} /> : null}
          {activeTab === "power" ? <PowerPanel artifact={artifact} /> : null}
          {activeTab === "validation" ? <ValidationPanel plan={plan} /> : null}
          {activeTab === "steps" ? <StepsPanel plan={plan} /> : null}

          <div className="border-line-soft bg-surface/60 flex flex-wrap items-center gap-3 rounded-xl border px-4 py-3">
            <FileJson className="text-faint size-4" />
            <p className="text-faint text-[11px]">
              Exports: wiring CSV, BOM CSV, KiCad/EasyEDA netlist, printable SVG, Markdown build
              guide, and the raw JSON contract.
            </p>
            <a
              href={api.exportUrl(projectId, "json")}
              download="electrical-plan.json"
              className="text-muted hover:text-signal ml-auto inline-flex items-center gap-1 text-[11px]"
            >
              <Download className="size-3" /> JSON
            </a>
          </div>
        </div>
      ) : null}
    </div>
  );
}
