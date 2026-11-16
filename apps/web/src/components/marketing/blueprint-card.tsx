import {
  ArrowRight,
  Bot,
  Check,
  ChevronRight,
  CircuitBoard,
  Coins,
  Cpu,
  Layers,
  Ruler,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";

const NODES = [
  { label: "Planner", detail: "spec draft", icon: Bot, state: "ready" },
  { label: "Components", detail: "12 parts", icon: Layers, state: "queued" },
  { label: "Wiring", detail: "5V · 2.1A", icon: CircuitBoard, state: "queued" },
  { label: "Firmware", detail: "Arduino", icon: Cpu, state: "queued" },
  { label: "Mechanical", detail: "4WD chassis", icon: Ruler, state: "queued" },
  { label: "Cost", detail: "$182 est.", icon: Coins, state: "queued" },
] as const;

export function BlueprintCard() {
  return (
    <div className="relative">
      <div className="bg-signal/[0.04] absolute -inset-6 rounded-[2rem] blur-2xl" aria-hidden />
      <div className="border-line bg-surface relative overflow-hidden rounded-2xl border shadow-[0_40px_120px_-40px_rgba(0,0,0,0.9)]">
        <div className="border-line-soft flex items-center justify-between border-b px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="bg-signal/80 size-2 rounded-full" />
            <span className="bg-warn/60 size-2 rounded-full" />
            <span className="bg-line size-2 rounded-full" />
            <span className="text-faint ml-2 font-mono text-[10px] tracking-[0.14em] uppercase">
              project / line-follower
            </span>
          </div>
          <Badge variant="signal">
            <Sparkles className="size-2.5" /> planning
          </Badge>
        </div>

        <div className="bg-blueprint relative p-5 sm:p-6">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <p className="text-faint font-mono text-[9px] tracking-[0.18em] uppercase">
                Robot specification
              </p>
              <h3 className="text-ink mt-1 text-lg font-medium tracking-tight">
                Classroom line follower
              </h3>
              <p className="text-muted mt-1 max-w-xs text-xs leading-relaxed">
                Follow a taped track, stop for obstacles, 30 min runtime. Budget $60.
              </p>
            </div>
            <div className="border-line bg-canvas/60 hidden shrink-0 rounded-lg border px-3 py-2 text-right sm:block">
              <p className="text-faint font-mono text-[9px] tracking-wider uppercase">Target</p>
              <p className="text-signal mt-0.5 font-mono text-sm">$58.40</p>
            </div>
          </div>

          <div className="border-line-soft bg-canvas/50 relative mb-5 overflow-hidden rounded-xl border p-4">
            <p className="text-faint mb-3 font-mono text-[9px] tracking-[0.18em] uppercase">
              Agent pipeline
            </p>
            <div className="space-y-2">
              {NODES.map((node, index) => (
                <div key={node.label} className="flex items-center gap-2.5">
                  <div
                    className={`flex size-7 shrink-0 items-center justify-center rounded-md border ${
                      index === 0
                        ? "border-signal/30 bg-signal/10 text-signal"
                        : "border-line bg-elevated text-faint"
                    }`}
                  >
                    <node.icon className="size-3.5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-3">
                      <span className={index === 0 ? "text-ink text-xs" : "text-muted text-xs"}>
                        {node.label}
                      </span>
                      <span className="text-faint font-mono text-[9px] tracking-wide">
                        {node.detail}
                      </span>
                    </div>
                    <div className="bg-raised mt-1 h-1 overflow-hidden rounded-full">
                      <div
                        className={
                          index === 0
                            ? "bg-signal h-full w-[68%] rounded-full"
                            : "bg-aqua h-full w-0 rounded-full"
                        }
                      />
                    </div>
                  </div>
                  {index === 0 ? (
                    <Check className="text-signal size-3 shrink-0" />
                  ) : (
                    <ChevronRight className="text-line size-3 shrink-0" />
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2">
            {[
              ["Platform", "Arduino"],
              ["Drive", "Differential"],
              ["Parts", "12 items"],
            ].map(([label, value]) => (
              <div
                key={label}
                className="border-line-soft bg-canvas/40 rounded-lg border px-2.5 py-2"
              >
                <p className="text-faint font-mono text-[8px] tracking-[0.14em] uppercase">
                  {label}
                </p>
                <p className="text-ink mt-1 truncate text-[11px]">{value}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="border-line-soft flex items-center justify-between border-t px-4 py-3">
          <div className="text-faint flex items-center gap-1.5 font-mono text-[9px] tracking-wide">
            <span className="bg-signal pulse-dot size-1.5 rounded-full" />
            orchestration ready
          </div>
          <span className="text-muted flex items-center gap-1 font-mono text-[9px]">
            open workspace <ArrowRight className="size-3" />
          </span>
        </div>
      </div>

      <div className="border-aqua/25 bg-canvas/90 text-aqua absolute -top-3 -right-2 hidden rotate-2 items-center gap-1.5 rounded-full border px-3 py-1.5 font-mono text-[9px] shadow-xl backdrop-blur sm:flex">
        <Sparkles className="size-3" /> agent contracts v1
      </div>
      <div className="border-line bg-canvas/90 text-muted absolute -bottom-4 -left-3 hidden -rotate-2 items-center gap-1.5 rounded-full border px-3 py-1.5 font-mono text-[9px] shadow-xl backdrop-blur sm:flex">
        M1 · foundation online
      </div>
    </div>
  );
}
