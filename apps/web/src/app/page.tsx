import {
  ArrowRight,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  CircuitBoard,
  FileCode2,
  Github,
  Layers,
  Lock,
  Sparkles,
  Workflow,
  Wrench,
} from "lucide-react";
import Link from "next/link";

import { Logo } from "@/components/brand/logo";
import { BlueprintCard } from "@/components/marketing/blueprint-card";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { CAPABILITIES } from "@/lib/constants";
import { cn } from "@/lib/utils";

const STEPS = [
  {
    number: "01",
    title: "Describe what you want to build",
    description:
      "Write it in plain language, or start from a proven template. Budget, skill level, and platform are enough to begin.",
    icon: Sparkles,
  },
  {
    number: "02",
    title: "Review a structured plan",
    description:
      "The Planner converts intent into a specification. You approve the requirements before any component is recommended.",
    icon: Workflow,
  },
  {
    number: "03",
    title: "Build with the full picture",
    description:
      "Move through components, wiring, firmware, mechanics, and cost — every artifact derived from the same approved spec.",
    icon: FileCode2,
  },
];

const PIPELINE = [
  { label: "Robot Planner", icon: Bot, accent: true },
  { label: "Component Research", icon: Layers },
  { label: "Electrical", icon: CircuitBoard },
  { label: "Programming", icon: FileCode2 },
  { label: "Mechanical", icon: Wrench },
  { label: "Cost", icon: CheckCircle2 },
];

export default function LandingPage() {
  return (
    <div className="relative overflow-hidden">
      <header className="bg-canvas/75 fixed inset-x-0 top-0 z-50 border-b border-white/[0.06] backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 sm:px-8">
          <Logo />
          <nav className="text-muted hidden items-center gap-7 text-[13px] md:flex">
            <a href="#capabilities" className="hover:text-ink transition-colors">
              Capabilities
            </a>
            <a href="#how-it-works" className="hover:text-ink transition-colors">
              How it works
            </a>
            <a href="#architecture" className="hover:text-ink transition-colors">
              Architecture
            </a>
          </nav>
          <div className="flex items-center gap-2">
            <a
              href="https://github.com/Abooubaker/robocraft"
              target="_blank"
              rel="noreferrer"
              className="text-muted hover:text-ink hidden size-9 items-center justify-center rounded-lg transition-colors hover:bg-white/5 sm:flex"
              aria-label="GitHub repository"
            >
              <Github className="size-4" />
            </a>
            <ButtonLink href="/dashboard" variant="secondary" size="sm" className="hidden sm:flex">
              Open workspace
            </ButtonLink>
            <ButtonLink href="/projects/new" size="sm">
              Start building <ArrowRight className="size-3.5" />
            </ButtonLink>
          </div>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="border-line-soft relative border-b pt-32 pb-20 sm:pt-40 sm:pb-28">
          <div className="bg-blueprint mask-fade-b pointer-events-none absolute inset-0 opacity-60" />
          <div className="bg-signal/[0.07] pointer-events-none absolute top-0 left-1/2 h-[520px] w-[900px] -translate-x-1/2 rounded-full blur-[120px]" />
          <div className="relative mx-auto grid max-w-7xl items-center gap-16 px-5 sm:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:gap-12">
            <div className="fade-up">
              <div className="border-signal/20 bg-signal/[0.06] mb-6 inline-flex items-center gap-2 rounded-full border px-3 py-1.5">
                <span className="bg-signal pulse-dot size-1.5 rounded-full" />
                <span className="text-signal font-mono text-[10px] tracking-[0.16em] uppercase">
                  M1 foundation · agents online
                </span>
              </div>

              <h1 className="text-ink max-w-xl text-[42px] leading-[1.04] font-medium tracking-[-0.035em] sm:text-[56px] lg:text-[60px]">
                Build your first robot
                <span className="text-gradient block">with a plan, not a guess.</span>
              </h1>

              <p className="text-muted mt-6 max-w-lg text-[15px] leading-relaxed sm:text-base">
                RoboCraft is an AI engineering copilot for robotics. Describe the robot you want.
                Get a structured specification, a compatible bill of materials, wiring, firmware,
                mechanical steps, and a real budget.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <ButtonLink href="/projects/new" size="lg">
                  Describe your robot <ArrowRight className="size-4" />
                </ButtonLink>
                <ButtonLink href="/dashboard" variant="secondary" size="lg">
                  Explore the workspace
                </ButtonLink>
              </div>

              <div className="text-faint mt-7 flex flex-wrap items-center gap-x-5 gap-y-2 text-[11px]">
                <span className="flex items-center gap-1.5">
                  <Lock className="size-3" /> No API keys required to explore
                </span>
                <span className="flex items-center gap-1.5">
                  <Github className="size-3" /> Open development roadmap
                </span>
              </div>
            </div>

            <div className="fade-up [animation-delay:120ms]">
              <BlueprintCard />
            </div>
          </div>
        </section>

        {/* Capability ticker */}
        <section className="border-line-soft bg-surface/40 border-b">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-x-8 gap-y-4 px-5 py-5 sm:px-8">
            <p className="text-faint font-mono text-[10px] tracking-[0.18em] uppercase">
              One workspace, five engineering disciplines
            </p>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
              {CAPABILITIES.map((capability) => (
                <span
                  key={capability.id}
                  className="text-muted flex items-center gap-1.5 font-mono text-[10px] tracking-wide"
                >
                  <capability.icon className="text-signal/70 size-3" />
                  {capability.title}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* Capabilities */}
        <section id="capabilities" className="relative py-24 sm:py-28">
          <div className="mx-auto max-w-7xl px-5 sm:px-8">
            <div className="mb-12 flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
              <div className="max-w-xl">
                <p className="text-signal mb-3 font-mono text-[11px] tracking-[0.2em] uppercase">
                  Capabilities
                </p>
                <h2 className="text-ink text-3xl font-medium tracking-[-0.025em] sm:text-4xl">
                  A complete engineering chain, not a chat window.
                </h2>
              </div>
              <p className="text-muted max-w-sm text-sm leading-relaxed">
                Every module consumes the same approved specification and hands structured artifacts
                to the next. Change one decision and the rest can be re-derived.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {CAPABILITIES.map((capability, index) => (
                <article
                  key={capability.id}
                  className={cn(
                    "group rounded-panel border-line-soft bg-surface hover:border-line relative flex flex-col justify-between overflow-hidden border p-6 transition-colors",
                    index === 0 && "lg:col-span-2",
                  )}
                >
                  <div className="bg-signal/[0.04] pointer-events-none absolute -top-16 -right-16 size-40 rounded-full blur-2xl transition-opacity group-hover:opacity-100" />
                  <div>
                    <div className="mb-6 flex items-start justify-between">
                      <div className="border-line bg-elevated text-signal flex size-10 items-center justify-center rounded-lg border">
                        <capability.icon className="size-4.5" strokeWidth={1.6} />
                      </div>
                      <span className="text-faint font-mono text-[10px] tracking-[0.16em]">
                        {capability.number} / {capability.milestone}
                      </span>
                    </div>
                    <h3 className="text-ink text-lg font-medium">{capability.title}</h3>
                    <p className="text-muted mt-2 max-w-xl text-sm leading-relaxed">
                      {capability.description}
                    </p>
                  </div>
                  <div className="text-faint mt-6 flex items-center gap-2 font-mono text-[9px] tracking-[0.14em] uppercase">
                    <span className="bg-line h-px w-5" />
                    planned · {capability.milestone}
                  </div>
                </article>
              ))}

              <article className="rounded-panel border-line flex flex-col justify-between border border-dashed bg-transparent p-6">
                <div>
                  <div className="border-line text-aqua mb-6 flex size-10 items-center justify-center rounded-lg border">
                    <ArrowUpRight className="size-4.5" strokeWidth={1.6} />
                  </div>
                  <h3 className="text-ink text-lg font-medium">Follow the build</h3>
                  <p className="text-muted mt-2 text-sm leading-relaxed">
                    The roadmap, architecture decisions, and agent contracts are public from day
                    one. Pick a milestone and watch it ship.
                  </p>
                </div>
                <a
                  href="https://github.com/Abooubaker/robocraft"
                  target="_blank"
                  rel="noreferrer"
                  className="text-signal hover:text-ink mt-6 flex items-center gap-2 text-xs transition-colors"
                >
                  View the repository <ArrowUpRight className="size-3.5" />
                </a>
              </article>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section
          id="how-it-works"
          className="border-line-soft bg-surface/30 border-y py-24 sm:py-28"
        >
          <div className="mx-auto max-w-7xl px-5 sm:px-8">
            <div className="mb-12 max-w-2xl">
              <p className="text-aqua mb-3 font-mono text-[11px] tracking-[0.2em] uppercase">
                How it works
              </p>
              <h2 className="text-ink text-3xl font-medium tracking-[-0.025em] sm:text-4xl">
                From a sentence to a build-ready plan.
              </h2>
            </div>

            <div className="rounded-panel border-line-soft bg-line-soft grid gap-px overflow-hidden border md:grid-cols-3">
              {STEPS.map((step) => (
                <div key={step.number} className="bg-surface p-7">
                  <div className="mb-8 flex items-center justify-between">
                    <span className="text-signal font-mono text-[11px] tracking-[0.16em]">
                      {step.number}
                    </span>
                    <step.icon className="text-faint size-4" strokeWidth={1.5} />
                  </div>
                  <h3 className="text-ink text-[17px] font-medium">{step.title}</h3>
                  <p className="text-muted mt-2.5 text-sm leading-relaxed">{step.description}</p>
                </div>
              ))}
            </div>

            <div className="rounded-panel border-line-soft bg-canvas/40 mt-8 flex flex-col items-start justify-between gap-4 border px-5 py-4 sm:flex-row sm:items-center">
              <p className="text-muted text-sm">
                <span className="text-ink">Independent agents.</span> Shared, typed contracts. One
                source of truth.
              </p>
              <Link
                href="/projects/new"
                className="text-signal hover:text-ink flex items-center gap-1.5 text-xs"
              >
                Start with a description <ArrowRight className="size-3.5" />
              </Link>
            </div>
          </div>
        </section>

        {/* Architecture */}
        <section id="architecture" className="py-24 sm:py-28">
          <div className="mx-auto grid max-w-7xl items-center gap-14 px-5 sm:px-8 lg:grid-cols-2">
            <div>
              <p className="text-signal mb-3 font-mono text-[11px] tracking-[0.2em] uppercase">
                Architecture
              </p>
              <h2 className="text-ink text-3xl font-medium tracking-[-0.025em] sm:text-4xl">
                Six specialists. One orchestrated pipeline.
              </h2>
              <p className="text-muted mt-4 max-w-lg text-sm leading-relaxed">
                The Robot Planner owns the specification. Every downstream agent reads only the
                artifacts it needs and writes back one typed result. That separation lets frontend,
                AI, electrical, and mechanical engineers work in parallel without blocking each
                other.
              </p>

              <ul className="mt-7 space-y-3">
                {[
                  "Provider-independent LLM boundary — swap models without touching agents",
                  "Strict JSON contracts exported for frontend and documentation",
                  "Every execution audited with inputs, outputs, tokens, and latency",
                  "Deterministic safety checks stay in code, not prompts",
                ].map((item) => (
                  <li key={item} className="text-muted flex items-start gap-2.5 text-sm">
                    <CheckCircle2 className="text-signal/80 mt-0.5 size-4 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>

              <div className="mt-8">
                <ButtonLink
                  href="https://github.com/Abooubaker/robocraft/blob/main/docs/ai-agents.md"
                  target="_blank"
                  rel="noreferrer"
                  variant="secondary"
                >
                  Read the agent architecture <ArrowUpRight className="size-3.5" />
                </ButtonLink>
              </div>
            </div>

            <div className="rounded-panel border-line-soft bg-surface border p-6 sm:p-8">
              <div className="mb-6 flex items-center justify-between">
                <p className="text-faint font-mono text-[10px] tracking-[0.16em] uppercase">
                  orchestration graph
                </p>
                <Badge variant="outline">contract v1</Badge>
              </div>
              <div className="space-y-2.5">
                {PIPELINE.map((node, index) => (
                  <div key={node.label} className="flex items-center gap-3">
                    <div
                      className={cn(
                        "flex size-9 shrink-0 items-center justify-center rounded-lg border",
                        node.accent
                          ? "border-signal/30 bg-signal/10 text-signal"
                          : "border-line bg-elevated text-muted",
                      )}
                    >
                      <node.icon className="size-4" strokeWidth={1.6} />
                    </div>
                    <div className="border-line-soft bg-canvas/40 flex h-9 flex-1 items-center justify-between rounded-lg border px-3.5">
                      <span className="text-ink text-[13px]">{node.label}</span>
                      <span className="text-faint font-mono text-[9px] tracking-wider uppercase">
                        {index === 0
                          ? "owns spec"
                          : index < 3
                            ? "depends on planner"
                            : "independent branch"}
                      </span>
                    </div>
                    {index < PIPELINE.length - 1 ? (
                      <div className="absolute hidden" aria-hidden />
                    ) : null}
                  </div>
                ))}
              </div>
              <div className="border-line text-faint mt-6 rounded-lg border border-dashed px-4 py-3 font-mono text-[10px] leading-relaxed">
                <span className="text-muted">shared_context</span> · specification → bom → wiring →
                firmware → assembly → budget
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="px-5 pb-24 sm:px-8">
          <div className="border-signal/20 bg-signal/[0.04] relative mx-auto max-w-7xl overflow-hidden rounded-2xl border px-6 py-14 text-center sm:px-12">
            <div className="bg-dot-grid pointer-events-none absolute inset-0 opacity-30" />
            <div className="bg-signal/10 pointer-events-none absolute -top-24 left-1/2 h-64 w-[600px] -translate-x-1/2 rounded-full blur-[80px]" />
            <div className="relative">
              <Badge variant="signal" className="mb-5">
                <Sparkles className="size-2.5" /> foundation release
              </Badge>
              <h2 className="text-ink mx-auto max-w-xl text-3xl font-medium tracking-[-0.025em] sm:text-4xl">
                Your first robot starts with a sentence.
              </h2>
              <p className="text-muted mx-auto mt-4 max-w-md text-sm leading-relaxed">
                Create a project, describe the goal, and explore the workspace the team is building
                on.
              </p>
              <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
                <ButtonLink href="/projects/new" size="lg">
                  Create a project <ArrowRight className="size-4" />
                </ButtonLink>
                <ButtonLink
                  href="https://github.com/Abooubaker/robocraft"
                  target="_blank"
                  rel="noreferrer"
                  variant="outline"
                  size="lg"
                >
                  <Github className="size-4" /> View on GitHub
                </ButtonLink>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-line-soft border-t">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-5 py-10 sm:px-8 md:flex-row md:items-center md:justify-between">
          <div>
            <Logo />
            <p className="text-faint mt-2 text-xs">
              AI-assisted robotics engineering. Built in the open.
            </p>
          </div>
          <div className="text-faint flex flex-wrap items-center gap-x-6 gap-y-2 font-mono text-[10px] tracking-wide uppercase">
            <Link href="/dashboard" className="hover:text-ink">
              Workspace
            </Link>
            <a
              href="https://github.com/Abooubaker/robocraft/blob/main/docs/architecture.md"
              target="_blank"
              rel="noreferrer"
              className="hover:text-ink"
            >
              Architecture
            </a>
            <a
              href="https://github.com/Abooubaker/robocraft/blob/main/CONTRIBUTING.md"
              target="_blank"
              rel="noreferrer"
              className="hover:text-ink"
            >
              Contributing
            </a>
            <span>© 2026 RoboCraft</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
