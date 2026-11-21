import { Bot, Check, ChevronRight, CircuitBoard, Coins, Cpu, Layers, Ruler } from "lucide-react";

import { Badge } from "@/components/ui/badge";

const NODES = [
  { label: "Planner", detail: "spec draft", icon: Bot, state: "ready" },
  { label: "Components", detail: "12 parts", icon: Layers, state: "queued" },
  { label: "Wiring", detail: "5V · 2.1A", icon: CircuitBoard, state: "queued" },
  { label: "Firmware", detail: "Arduino", icon: Cpu, state: "queued" },
  { label: "Mechanical", detail: "4WD chassis", icon: Ruler, state: "queued" },
  { label: "Cost", detail: "182 JD est.", icon: Coins, state: "queued" },
] as const;

export function BlueprintCard() {
  return (
    <div className="relative">
      <span className="bg-canvas text-faint absolute -top-2 left-3 px-1.5 font-mono text-[9px] tracking-[0.18em] uppercase">
        Drawing 01
      </span>
      <div className="registration-mark border-line-soft bg-canvas/50 relative overflow-hidden border">
        <div className="border-line-soft flex items-center justify-between border-b px-4 py-2.5">
          <span className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
            Fig. 01 / project schematic
          </span>
          <Badge variant="outline">Rev 0.1</Badge>
        </div>

        <div className="bg-blueprint p-5 sm:p-6">
          <div className="flex items-start justify-between gap-5">
            <div className="min-w-0">
              <p className="text-faint font-mono text-[9px] tracking-[0.18em] uppercase">
                Spec / line-follower
              </p>
              <h3 className="text-ink mt-1.5 text-lg font-medium tracking-tight">
                Classroom line follower
              </h3>
              <p className="text-muted mt-1.5 max-w-xs text-xs leading-relaxed">
                Follow a taped track, stop for obstacles, 30 min runtime. Budget 60 JD.
              </p>
            </div>
            <div className="border-line-soft shrink-0 border-l pl-4 text-right">
              <p className="text-faint font-mono text-[9px] tracking-wider uppercase">Target</p>
              <p className="text-signal mt-1 font-mono text-base">58.40 JD</p>
            </div>
          </div>

          <div className="border-line-soft mt-6 border-t pt-4">
            <div className="flex items-center justify-between">
              <p className="text-faint font-mono text-[9px] tracking-[0.18em] uppercase">
                Agent pipeline
              </p>
              <p className="text-faint font-mono text-[9px]">06 nodes</p>
            </div>
            <div className="divide-line-soft mt-3 divide-y">
              {NODES.map((node, index) => (
                <div key={node.label} className="flex items-center gap-3 py-2">
                  <span className="text-faint w-5 shrink-0 font-mono text-[9px]">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <node.icon
                    className={index === 0 ? "text-signal size-3.5" : "text-faint size-3.5"}
                  />
                  <span
                    className={
                      index === 0 ? "text-ink flex-1 text-xs" : "text-muted flex-1 text-xs"
                    }
                  >
                    {node.label}
                  </span>
                  <span className="text-faint font-mono text-[9px] tracking-wide">
                    {node.detail}
                  </span>
                  {index === 0 ? (
                    <Check className="text-signal size-3 shrink-0" />
                  ) : (
                    <ChevronRight className="text-line size-3 shrink-0" />
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="divide-line-soft border-line-soft mt-6 grid grid-cols-3 divide-x border-t pt-4">
            {[
              ["Platform", "Arduino"],
              ["Drive", "Differential"],
              ["Parts", "12 items"],
            ].map(([label, value]) => (
              <div key={label} className="px-3 first:pl-0 last:pr-0">
                <p className="text-faint font-mono text-[8px] tracking-[0.14em] uppercase">
                  {label}
                </p>
                <p className="text-ink mt-1 truncate font-mono text-[11px]">{value}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="border-line-soft flex items-center justify-between border-t px-4 py-2.5">
          <span className="text-faint flex items-center gap-2 font-mono text-[9px] tracking-wide uppercase">
            <span className="bg-signal pulse-dot size-1.5 rounded-full" />
            orchestration ready
          </span>
          <span className="text-muted font-mono text-[9px]">open workspace →</span>
        </div>
      </div>
    </div>
  );
}
