"use client";

import { ArrowRight, CheckCircle2, CircuitBoard, Code2, Github, Layers, Ruler } from "lucide-react";
import Link from "next/link";

import { LanguageToggle } from "@/components/brand/language-toggle";
import { Logo } from "@/components/brand/logo";
import { ScrollCompanion } from "@/components/brand/scroll-companion";
import { BlueprintCard } from "@/components/marketing/blueprint-card";
import { ButtonLink } from "@/components/ui/button";
import { DEMO_MODE, DEMO_PROJECT_ID } from "@/lib/constants";
import { useDocumentLanguage, useLang, type Lang } from "@/lib/i18n";

type Item = { title: string; description: string };

type Copy = {
  github: string;
  openDemoShort: string;
  startBuild: string;
  badgeDemo: string;
  badgeFlow: string;
  heroLead: string;
  heroAccent: string;
  heroBody: string;
  openDemo: string;
  describe: string;
  seeCode: string;
  openWorkspace: string;
  checks: string[];
  steps: Item[];
  eyebrow: string;
  resultsTitle: string;
  resultsBody: string;
  results: Item[];
  resultsNote: string;
  ctaTitle: string;
  ctaBody: string;
  viewGithub: string;
  tagline: string;
  workspace: string;
  docs: string;
  copyright: string;
};

const COPY: Record<Lang, Copy> = {
  en: {
    github: "GitHub repository",
    openDemoShort: "Open demo build",
    startBuild: "Start a build",
    badgeDemo: "Live demo · real engine output",
    badgeFlow: "From idea to build in one flow",
    heroLead: "Build a robot",
    heroAccent: "without guessing.",
    heroBody:
      "Describe what you want to build. Albayraq identifies the robot, prices the parts at your stores, and generates the schematic, code, 3D print price, and docs.",
    openDemo: "Open the demo build",
    describe: "Describe your robot",
    seeCode: "See the generated code",
    openWorkspace: "Open workspace",
    checks: ["Six short questions", "Nothing is ordered", "Prices labelled as estimates"],
    steps: [
      {
        title: "Describe it",
        description: "One sentence is enough. We name the robot and identify the type.",
      },
      {
        title: "Confirm the details",
        description: "Pick your stores, languages, controller, and whether you want a custom PCB.",
      },
      {
        title: "Get the whole build",
        description: "Sourced prices, schematic, code, 3D print price, budget, and documentation.",
      },
    ],
    eyebrow: "What you get",
    resultsTitle: "One build. Every artifact.",
    resultsBody:
      "Everything is derived from the same confirmed answers and validated pin map — not generated in isolation.",
    results: [
      { title: "Parts & prices", description: "Each part at every store, cheapest first" },
      { title: "Schematic", description: "Every pin, net, and destination" },
      { title: "Code", description: "Multi-file bundles for every language" },
      { title: "3D & print price", description: "STL, weight, and JOD material chart" },
    ],
    resultsNote:
      "Also included: a JOD budget roll-up and a documentation set covering sourcing, wiring, firmware, mechanical pricing, safety, and decisions.",
    ctaTitle: "Start with a sentence.",
    ctaBody:
      "Six questions later you have prices, a schematic, code, a 3D print price, and a documented build plan.",
    viewGithub: "View on GitHub",
    tagline: "AI-assisted robotics engineering.",
    workspace: "Workspace",
    docs: "Docs",
    copyright: "© 2026 Albayraq",
  },
  ar: {
    github: "مستودع GitHub",
    openDemoShort: "افتح النسخة التجريبية",
    startBuild: "ابدأ بناءً جديدًا",
    badgeDemo: "عرض مباشر · مخرجات حقيقية من المحرك",
    badgeFlow: "من الفكرة إلى البناء في مسار واحد",
    heroLead: "ابنِ روبوتك",
    heroAccent: "بدون تخمين.",
    heroBody:
      "صِف الروبوت الذي تريد بناءه. يتعرّف البيرق على نوعه، ويسعّر القطع في متاجرك، ويولّد المخطط الكهربائي والكود وسعر الطباعة ثلاثية الأبعاد والتوثيق.",
    openDemo: "افتح النسخة التجريبية",
    describe: "صِف روبوتك",
    seeCode: "اطّلع على الكود المُولَّد",
    openWorkspace: "افتح مساحة العمل",
    checks: ["ست أسئلة قصيرة", "لا يتم طلب أي شيء", "الأسعار موسومة كتقديرات"],
    steps: [
      {
        title: "صِفه",
        description: "جملة واحدة تكفي. نسمّي الروبوت ونحدد نوعه.",
      },
      {
        title: "أكّد التفاصيل",
        description: "اختر المتاجر واللغات والمتحكّم، وهل تريد لوحة PCB مخصّصة.",
      },
      {
        title: "احصل على البناء كاملًا",
        description:
          "أسعار موثّقة، ومخطط كهربائي، وكود، وسعر الطباعة ثلاثية الأبعاد، وميزانية، وتوثيق.",
      },
    ],
    eyebrow: "ما تحصل عليه",
    resultsTitle: "بناء واحد. كل المخرجات.",
    resultsBody:
      "كل شيء مشتق من نفس الإجابات المؤكدة وخريطة الأطراف المعتمدة، وليس مولّدًا بمعزل عن بعضه.",
    results: [
      { title: "القطع والأسعار", description: "كل قطعة في كل متجر، من الأرخص" },
      { title: "المخطط الكهربائي", description: "كل طرف وشبكة ووجهة" },
      { title: "الكود", description: "حِزم متعددة الملفات لكل لغة" },
      { title: "الطباعة ثلاثية الأبعاد", description: "ملف STL والوزن وجدول المواد بالدينار" },
    ],
    resultsNote:
      "يتضمن أيضًا: ملخص ميزانية بالدينار الأردني، ومجموعة توثيق تغطي المصادر والتوصيل والبرمجيات الثابتة والتسعير الميكانيكي والسلامة والقرارات.",
    ctaTitle: "ابدأ بجملة واحدة.",
    ctaBody:
      "بعد ست أسئلة تحصل على الأسعار والمخطط الكهربائي والكود وسعر الطباعة ثلاثية الأبعاد وخطة بناء موثّقة.",
    viewGithub: "عرض على GitHub",
    tagline: "هندسة الروبوتات بمساعدة الذكاء الاصطناعي.",
    workspace: "مساحة العمل",
    docs: "التوثيق",
    copyright: "© 2026 البيرق",
  },
};

const STEP_NUMBERS = ["01", "02", "03"];
const RESULT_ICONS = [Layers, CircuitBoard, Code2, Ruler];
const RESULT_KEYS = ["parts", "schematic", "code", "print"];

export default function LandingPage() {
  const { lang } = useLang();
  useDocumentLanguage(lang);
  const c = COPY[lang];
  const primaryHref = DEMO_MODE ? `/projects/${DEMO_PROJECT_ID}` : "/projects/new";

  return (
    <div className="mc-theme relative overflow-hidden">
      <ScrollCompanion />
      <header className="bg-canvas/75 fixed inset-x-0 top-0 z-50 border-b border-white/[0.06] backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-8">
          <Logo />
          <div className="flex items-center gap-3">
            <LanguageToggle />
            <a
              href="https://github.com/Abooubaker/blueprints-baker"
              target="_blank"
              rel="noreferrer"
              className="text-muted hover:text-ink hidden size-9 items-center justify-center rounded-lg transition-colors hover:bg-white/5 sm:flex"
              aria-label={c.github}
            >
              <Github className="size-4" />
            </a>
            <ButtonLink href={primaryHref} size="sm" variant="secondary" className="mc-btn">
              {DEMO_MODE ? c.openDemoShort : c.startBuild}
            </ButtonLink>
          </div>
        </div>
      </header>

      <main>
        <section className="border-line-soft relative border-b pt-32 pb-20 sm:pt-40 sm:pb-24">
          <div className="bg-blueprint mask-fade-b pointer-events-none absolute inset-0 opacity-60" />
          <div className="bg-signal/[0.07] pointer-events-none absolute top-0 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full blur-[120px]" />
          <div aria-hidden="true" className="voxel-field">
            <span className="voxel voxel-gold" />
            <span className="voxel voxel-burgundy" />
            <span className="voxel voxel-champagne" />
            <span className="voxel voxel-gold" />
            <span className="voxel voxel-burgundy" />
            <span className="voxel voxel-champagne" />
            <span className="voxel voxel-gold" />
          </div>
          <div aria-hidden="true" className="mc-terrain" />
          <div className="relative mx-auto grid max-w-6xl items-center gap-14 px-5 sm:px-8 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="fade-up">
              <div className="border-signal/20 bg-signal/[0.06] mb-6 inline-flex items-center gap-2 rounded-full border px-3 py-1.5">
                <span className="bg-signal pulse-dot size-1.5 rounded-full" />
                <span className="pixel text-signal font-mono text-[10px] tracking-[0.16em] uppercase">
                  {DEMO_MODE ? c.badgeDemo : c.badgeFlow}
                </span>
              </div>

              <h1 className="mc-title text-ink max-w-xl text-[42px] leading-[1.04] font-medium tracking-[-0.035em] sm:text-[54px]">
                {c.heroLead}
                <span className="text-gradient block">{c.heroAccent}</span>
              </h1>

              <p className="text-muted mt-6 max-w-lg text-[15px] leading-relaxed">{c.heroBody}</p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <ButtonLink href={primaryHref} size="lg" className="mc-btn">
                  {DEMO_MODE ? c.openDemo : c.describe}{" "}
                  <ArrowRight className="size-4 rtl:rotate-180" />
                </ButtonLink>
                <ButtonLink
                  href={DEMO_MODE ? `/projects/${DEMO_PROJECT_ID}/programming` : "/dashboard"}
                  variant="secondary"
                  size="lg"
                  className="mc-btn"
                >
                  {DEMO_MODE ? c.seeCode : c.openWorkspace}
                </ButtonLink>
              </div>

              <div className="text-faint mt-7 flex flex-wrap items-center gap-x-5 gap-y-2 text-[11px]">
                {c.checks.map((check) => (
                  <span key={check} className="flex items-center gap-1.5">
                    <CheckCircle2 className="text-signal/70 size-3" /> {check}
                  </span>
                ))}
              </div>
            </div>

            <div dir="ltr" className="fade-up [animation-delay:120ms]">
              <BlueprintCard />
            </div>
          </div>
        </section>

        <section className="border-line-soft bg-surface/30 border-b py-20">
          <div className="mx-auto max-w-6xl px-5 sm:px-8">
            <div className="rounded-panel border-line-soft bg-line-soft grid gap-px overflow-hidden border md:grid-cols-3">
              {c.steps.map((step, index) => (
                <div key={STEP_NUMBERS[index]} className="bg-surface p-7">
                  <span className="pixel text-signal font-mono text-[11px] tracking-[0.16em]">
                    {STEP_NUMBERS[index]}
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
              <p className="pixel text-signal mb-3 font-mono text-[11px] tracking-[0.2em] uppercase">
                {c.eyebrow}
              </p>
              <h2 className="pixel-title text-ink text-3xl font-medium tracking-[-0.025em] sm:text-4xl">
                {c.resultsTitle}
              </h2>
              <p className="text-muted mt-3 text-sm leading-relaxed">{c.resultsBody}</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {c.results.map((item, index) => {
                const Icon = RESULT_ICONS[index];
                return (
                  <div
                    key={RESULT_KEYS[index]}
                    className="block-bevel rounded-panel border-line-soft bg-surface border p-5"
                  >
                    <div className="border-line bg-elevated text-signal flex size-9 items-center justify-center rounded-lg border">
                      <Icon className="size-4" strokeWidth={1.6} />
                    </div>
                    <h3 className="text-ink mt-4 text-sm font-medium">{item.title}</h3>
                    <p className="text-faint mt-1.5 text-[11px] leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                );
              })}
            </div>
            <p className="text-faint mt-5 text-[11px]">{c.resultsNote}</p>
          </div>
        </section>

        <section className="px-5 pb-24 sm:px-8">
          <div className="block-bevel border-signal/20 bg-signal/[0.04] relative mx-auto max-w-6xl overflow-hidden rounded-2xl border px-6 py-14 text-center sm:px-12">
            <div className="bg-dot-grid pointer-events-none absolute inset-0 opacity-30" />
            <div className="bg-signal/10 pointer-events-none absolute -top-24 left-1/2 h-64 w-[600px] -translate-x-1/2 rounded-full blur-[80px]" />
            <div className="relative">
              <h2 className="pixel-title text-ink mx-auto max-w-xl text-3xl font-medium tracking-[-0.025em] sm:text-4xl">
                {c.ctaTitle}
              </h2>
              <p className="text-muted mx-auto mt-4 max-w-md text-sm leading-relaxed">
                {c.ctaBody}
              </p>
              <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
                <ButtonLink href={primaryHref} size="lg" className="mc-btn">
                  {DEMO_MODE ? c.openDemo : c.describe}{" "}
                  <ArrowRight className="size-4 rtl:rotate-180" />
                </ButtonLink>
                <ButtonLink
                  href="https://github.com/Abooubaker/blueprints-baker"
                  target="_blank"
                  rel="noreferrer"
                  variant="outline"
                  size="lg"
                  className="mc-btn"
                >
                  <Github className="size-4" /> {c.viewGithub}
                </ButtonLink>
              </div>
            </div>
          </div>
        </section>
      </main>

      <div aria-hidden="true" className="ground-strip" />

      <footer className="border-line-soft border-t">
        <div className="mx-auto flex max-w-6xl flex-col gap-5 px-5 py-9 sm:px-8 md:flex-row md:items-center md:justify-between">
          <div>
            <Logo />
            <p className="text-faint mt-2 text-xs">{c.tagline}</p>
          </div>
          <div className="text-faint flex flex-wrap items-center gap-x-5 gap-y-2 font-mono text-[10px] tracking-wide uppercase">
            <Link href="/dashboard" className="hover:text-ink">
              {c.workspace}
            </Link>
            <a
              href="https://github.com/Abooubaker/blueprints-baker/tree/main/docs"
              target="_blank"
              rel="noreferrer"
              className="hover:text-ink"
            >
              {c.docs}
            </a>
            <span>{c.copyright}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
