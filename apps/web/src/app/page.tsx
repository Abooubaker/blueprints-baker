import { ArrowRight, CheckCircle2, CircuitBoard, Code2, Github, Layers, Ruler } from "lucide-react";
import Link from "next/link";

import { Logo } from "@/components/brand/logo";
import { BlueprintCard } from "@/components/marketing/blueprint-card";
import { ButtonLink } from "@/components/ui/button";
import { DEMO_MODE, DEMO_PROJECT_ID } from "@/lib/constants";

const STEPS = [
  {
    number: "01",
    title: "Describe it",
    description: "One sentence is enough. We name the robot and identify the type.",
  },
  {
    number: "02",
    title: "Confirm the details",
    description: "Pick your stores, languages, controller, and whether you want a custom PCB.",
  },
  {
    number: "03",
    title: "Get the whole build",
    description: "Sourced prices, schematic, code, 3D print price, budget, and documentation.",
  },
];

const RESULTS = [
  {
    title: "Parts & prices",
    description: "Each part at every store, cheapest first",
    icon: Layers,
  },
  { title: "Schematic", description: "Every pin, net, and destination", icon: CircuitBoard },
  { title: "Code", description: "Multi-file bundles for every language", icon: Code2 },
  { title: "3D & print price", description: "STL, weight, and JOD material chart", icon: Ruler },
];

export default function LandingPage() {
  const primaryHref = DEMO_MODE ? `/projects/${DEMO_PROJECT_ID}` : "/projects/new";

  return (
    <div className="relative overflow-hidden">
      <header className="bg-canvas/75 fixed inset-x-0 top-0 z-50 border-b border-white/[0.06] backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-8">
          <Logo />
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/Abooubaker/blueprints-baker"
              target="_blank"
              rel="noreferrer"
              className="text-muted hover:text-ink hidden size-9 items-center justify-center rounded-lg transition-colors hover:bg-white/5 sm:flex"
              aria-label="GitHub repository"
            >
              <Github className="size-4" />
            </a>
            <ButtonLink href={primaryHref} size="sm" variant="secondary">
              {DEMO_MODE ? "Open demo build" : "Start a build"}
            </ButtonLink>
          </div>
        </div>
      </header>

      <main>
        <section className="border-line-soft relative border-b pt-32 pb-20 sm:pt-40 sm:pb-24">
          <div className="bg-blueprint mask-fade-b pointer-events-none absolute inset-0 opacity-60" />
          <div className="bg-signal/[0.07] pointer-events-none absolute top-0 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full blur-[120px]" />
          <div className="relative mx-auto grid max-w-6xl items-center gap-14 px-5 sm:px-8 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="fade-up">
              <div className="border-signal/20 bg-signal/[0.06] mb-6 inline-flex items-center gap-2 rounded-full border px-3 py-1.5">
                <span className="bg-signal pulse-dot size-1.5 rounded-full" />
                <span className="text-signal font-mono text-[10px] tracking-[0.16em] uppercase">
                  {DEMO_MODE ? "Live demo · real engine output" : "From idea to build in one flow"}
                </span>
              </div>

              <h1 className="text-ink max-w-xl text-[42px] leading-[1.04] font-medium tracking-[-0.035em] sm:text-[54px]">
                Build a robot
                <span className="text-gradient block">without guessing.</span>
              </h1>

              <p className="text-muted mt-6 max-w-lg text-[15px] leading-relaxed">
                Describe what you want to build. Albayraq identifies the robot, prices the parts at
                your stores, and generates the schematic, code, 3D print price, and docs.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <ButtonLink href={primaryHref} size="lg">
                  {DEMO_MODE ? "Open the demo build" : "Describe your robot"}{" "}
                  <ArrowRight className="size-4" />
                </ButtonLink>
                <ButtonLink
                  href={DEMO_MODE ? `/projects/${DEMO_PROJECT_ID}/programming` : "/dashboard"}
                  variant="secondary"
                  size="lg"
                >
                  {DEMO_MODE ? "See the generated code" : "Open workspace"}
                </ButtonLink>
              </div>

              <div className="text-faint mt-7 flex flex-wrap items-center gap-x-5 gap-y-2 text-[11px]">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="text-signal/70 size-3" /> Six short questions
                </span>
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="text-signal/70 size-3" /> Nothing is ordered
                </span>
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="text-signal/70 size-3" /> Prices labelled as estimates
                </span>
              </div>
            </div>

            <div className="fade-up [animation-delay:120ms]">
              <BlueprintCard />
            </div>
          </div>
        </section>

        <section className="border-line-soft bg-surface/30 border-b py-20">
          <div className="mx-auto max-w-6xl px-5 sm:px-8">
            <div className="rounded-panel border-line-soft bg-line-soft grid gap-px overflow-hidden border md:grid-cols-3">
              {STEPS.map((step) => (
                <div key={step.number} className="bg-surface p-7">
                  <span className="text-signal font-mono text-[11px] tracking-[0.16em]">
                    {step.number}
                  </span>
                  <h2 className="text-ink mt-5 text-[17px] font-medium">{step.title}</h2>
                  <p className="text-muted mt-2 text-sm leading-relaxed">{step.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20">
          <div className="mx-auto max-w-6xl px-5 sm:px-8">
            <div className="mb-10 max-w-xl">
              <p className="text-signal mb-3 font-mono text-[11px] tracking-[0.2em] uppercase">
                What you get
              </p>
              <h2 className="text-ink text-3xl font-medium tracking-[-0.025em] sm:text-4xl">
                One build. Every artifact.
              </h2>
              <p className="text-muted mt-3 text-sm leading-relaxed">
                Everything is derived from the same confirmed answers and validated pin map — not
                generated in isolation.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {RESULTS.map((item) => (
                <div
                  key={item.title}
                  className="rounded-panel border-line-soft bg-surface border p-5"
                >
                  <div className="border-line bg-elevated text-signal flex size-9 items-center justify-center rounded-lg border">
                    <item.icon className="size-4" strokeWidth={1.6} />
                  </div>
                  <h3 className="text-ink mt-4 text-sm font-medium">{item.title}</h3>
                  <p className="text-faint mt-1.5 text-[11px] leading-relaxed">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
            <p className="text-faint mt-5 text-[11px]">
              Also included: a JOD budget roll-up and a documentation set covering sourcing, wiring,
              firmware, mechanical pricing, safety, and decisions.
            </p>
          </div>
        </section>

        <section className="px-5 pb-24 sm:px-8">
          <div className="border-signal/20 bg-signal/[0.04] relative mx-auto max-w-6xl overflow-hidden rounded-2xl border px-6 py-14 text-center sm:px-12">
            <div className="bg-dot-grid pointer-events-none absolute inset-0 opacity-30" />
            <div className="bg-signal/10 pointer-events-none absolute -top-24 left-1/2 h-64 w-[600px] -translate-x-1/2 rounded-full blur-[80px]" />
            <div className="relative">
              <h2 className="text-ink mx-auto max-w-xl text-3xl font-medium tracking-[-0.025em] sm:text-4xl">
                Start with a sentence.
              </h2>
              <p className="text-muted mx-auto mt-4 max-w-md text-sm leading-relaxed">
                Six questions later you have prices, a schematic, code, a 3D print price, and a
                documented build plan.
              </p>
              <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
                <ButtonLink href={primaryHref} size="lg">
                  {DEMO_MODE ? "Open the demo build" : "Describe your robot"}{" "}
                  <ArrowRight className="size-4" />
                </ButtonLink>
                <ButtonLink
                  href="https://github.com/Abooubaker/blueprints-baker"
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
        <div className="mx-auto flex max-w-6xl flex-col gap-5 px-5 py-9 sm:px-8 md:flex-row md:items-center md:justify-between">
          <div>
            <Logo />
            <p className="text-faint mt-2 text-xs">AI-assisted robotics engineering.</p>
          </div>
          <div className="text-faint flex flex-wrap items-center gap-x-5 gap-y-2 font-mono text-[10px] tracking-wide uppercase">
            <Link href="/dashboard" className="hover:text-ink">
              Workspace
            </Link>
            <a
              href="https://github.com/Abooubaker/blueprints-baker/tree/main/docs"
              target="_blank"
              rel="noreferrer"
              className="hover:text-ink"
            >
              Docs
            </a>
            <span>© 2026 Albayraq</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
