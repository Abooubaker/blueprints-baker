"use client";

import {
  ArrowLeft,
  ArrowRight,
  Bot,
  Check,
  CheckCircle2,
  CircuitBoard,
  Code2,
  Cpu,
  Loader2,
  ShoppingCart,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldHint, Input, Label, Textarea } from "@/components/ui/form";
import { Progress } from "@/components/ui/misc";
import { api, ApiError } from "@/lib/api";
import {
  CODE_LANGUAGES,
  CONTROLLER_FAMILIES,
  EXAMPLE_PROMPTS,
  ROBOT_TYPES,
  STORES,
} from "@/lib/constants";
import type {
  BuildPreferences,
  CodeLanguage,
  Difficulty,
  RobotIdentification,
  RobotType,
  StoreName,
  TargetPlatform,
} from "@/lib/types";
import { cn, titleCase } from "@/lib/utils";

const STEPS = [
  { title: "Describe", icon: Sparkles },
  { title: "Confirm robot", icon: Bot },
  { title: "Stores", icon: ShoppingCart },
  { title: "Languages", icon: Code2 },
  { title: "Hardware", icon: Cpu },
  { title: "Build", icon: CircuitBoard },
] as const;

const DEFAULT_SHOPS: StoreName[] = ["temu", "mikroelectron", "waslleh", "amazon"];
const DEFAULT_LANGUAGES: CodeLanguage[] = ["python", "cpp"];

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

function OptionTile({
  selected,
  onClick,
  title,
  description,
  icon,
}: {
  selected: boolean;
  onClick: () => void;
  title: string;
  description: string;
  icon?: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        "flex items-start gap-3 rounded-lg border px-3.5 py-3 text-left transition-colors",
        selected
          ? "border-signal/40 bg-signal/[0.07]"
          : "border-line bg-canvas/40 hover:border-[#2d6894]",
      )}
    >
      <span
        className={cn(
          "mt-0.5 flex size-4 shrink-0 items-center justify-center rounded border",
          selected ? "border-signal bg-signal text-signal-ink" : "border-line bg-canvas",
        )}
      >
        {selected ? <Check className="size-3" strokeWidth={3} /> : null}
      </span>
      {icon ? <span className="text-faint mt-0.5 shrink-0">{icon}</span> : null}
      <span className="min-w-0">
        <span className="text-ink block text-[12.5px] font-medium">{title}</span>
        <span className="text-faint mt-0.5 block text-[10.5px] leading-snug">{description}</span>
      </span>
    </button>
  );
}

export function GuidedWizard() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [description, setDescription] = useState("");
  const [identification, setIdentification] = useState<RobotIdentification | null>(null);
  const [identifying, setIdentifying] = useState(false);
  const [name, setName] = useState("");
  const [robotType, setRobotType] = useState<RobotType>("custom");
  const [difficulty, setDifficulty] = useState<Difficulty>("beginner");
  const [platform, setPlatform] = useState<TargetPlatform>("undecided");
  const [shops, setShops] = useState<StoreName[]>(DEFAULT_SHOPS);
  const [languages, setLanguages] = useState<CodeLanguage[]>(DEFAULT_LANGUAGES);
  const [controllers, setControllers] = useState<string[]>([]);
  const [controllerNotes, setControllerNotes] = useState("");
  const [customPcb, setCustomPcb] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [progressLabel, setProgressLabel] = useState("");

  const canContinue =
    step === 0
      ? description.trim().length >= 12
      : step === 2
        ? shops.length > 0
        : step === 3
          ? languages.length > 0
          : true;

  async function identify() {
    setError(null);
    setIdentifying(true);
    try {
      const result = await api.identifyRobot(description.trim());
      setIdentification(result);
      setName(result.proposed_name);
      setRobotType(result.robot_type);
      setDifficulty(result.suggested_difficulty);
      setPlatform(result.suggested_platform);
      setStep(1);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not identify the robot. Check that the API is running.",
      );
    } finally {
      setIdentifying(false);
    }
  }

  async function build() {
    setError(null);
    setSubmitting(true);
    try {
      setProgressLabel("Creating project…");
      const project = await api.createProject({
        name: name.trim() || identification?.proposed_name || "Robot project",
        description: description.trim(),
        robot_type: robotType,
        difficulty,
        target_platform: platform,
        budget_max_usd: null,
      });
      const preferences: BuildPreferences = {
        description: description.trim(),
        robot_name: project.name,
        robot_type: robotType,
        difficulty,
        shops,
        languages,
        controllers,
        controller_notes: controllerNotes.trim(),
        custom_pcb: customPcb,
        confirmed: true,
        budget_max_usd: null,
        identification_rationale: identification?.rationale ?? "",
        identification_confidence: identification?.confidence ?? 0,
      };
      setProgressLabel("Saving your answers…");
      await api.savePreferences(project.id, preferences);
      setProgressLabel("Finding parts, wiring, code, 3D price, and docs…");
      await api.generateBuild(project.id);
      router.push(`/projects/${project.id}`);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "The build could not finish. Check that the API and database are running.",
      );
      setSubmitting(false);
      setProgressLabel("");
    }
  }

  const selectedRobot = ROBOT_TYPES.find((item) => item.value === robotType) ?? ROBOT_TYPES.at(-1)!;

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-7">
        <div className="mb-3 flex items-center justify-between">
          <p className="text-faint font-mono text-[10px] tracking-[0.18em] uppercase">
            Step {step + 1} of {STEPS.length} · {STEPS[step]!.title}
          </p>
          <span className="text-faint font-mono text-[10px]">
            {Math.round(((step + 1) / STEPS.length) * 100)}%
          </span>
        </div>
        <Progress value={((step + 1) / STEPS.length) * 100} />
        <div className="mt-3 flex flex-wrap gap-1.5">
          {STEPS.map((item, index) => (
            <span
              key={item.title}
              className={cn(
                "flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[9px] uppercase",
                index === step
                  ? "border-signal/30 bg-signal/[0.07] text-signal"
                  : index < step
                    ? "border-line bg-canvas/40 text-muted"
                    : "border-line-soft text-faint border-dashed",
              )}
            >
              {index < step ? <Check className="size-2.5" /> : <item.icon className="size-2.5" />}
              {item.title}
            </span>
          ))}
        </div>
      </div>

      <Card className="panel-sheen">
        <CardHeader className="pb-4">
          <CardTitle className="text-base">
            {step === 0
              ? "What do you want to build?"
              : step === 1
                ? "Is this the right robot?"
                : step === 2
                  ? "Where should we price parts?"
                  : step === 3
                    ? "Which languages do you want?"
                    : step === 4
                      ? "What hardware do you have?"
                      : "Ready to generate your build"}
          </CardTitle>
          <p className="text-muted mt-1 text-xs leading-relaxed">
            {step === 0
              ? "Describe it in plain language. Blueprints Baker will name it and identify the robot type, then ask you to confirm."
              : step === 1
                ? "Nothing is ordered yet. Confirm or correct the name and type before pricing."
                : step === 2
                  ? "Every part is priced at each selected store and sorted cheapest first. Prices are labelled estimates."
                  : step === 3
                    ? "You will get a multi-file code bundle for every language, all from the same validated pin map."
                    : step === 4
                      ? "Controllers are optional. Leave them blank and the planner will choose a platform. A custom PCB is usually not needed for a first build."
                      : "One click runs the full pipeline and opens your results: prices, schematic, code, 3D price, and documentation."}
          </p>
        </CardHeader>

        <CardContent className="space-y-5">
          {step === 0 ? (
            <>
              <Field>
                <Label htmlFor="description">Describe the robot</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value.slice(0, 2000))}
                  placeholder="e.g. A small four-wheel rover that drives on my patio, avoids obstacles with an ultrasonic sensor, and streams distance readings over Wi-Fi."
                  className="min-h-40"
                  autoFocus
                />
                <div className="flex items-center justify-between gap-3">
                  <FieldHint>
                    Include what it should do, where it runs, and anything you already own.
                  </FieldHint>
                  <span className="text-faint shrink-0 font-mono text-[10px]">
                    {description.length}/2000
                  </span>
                </div>
              </Field>
              <div>
                <p className="text-faint mb-2 text-[11px]">Start from an example</p>
                <div className="flex flex-wrap gap-2">
                  {EXAMPLE_PROMPTS.map((example) => (
                    <button
                      key={example.title}
                      type="button"
                      onClick={() => setDescription(example.text)}
                      className="border-line bg-canvas/50 text-muted hover:border-signal/30 hover:text-ink flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[11px] transition-colors"
                    >
                      <Sparkles className="text-signal/70 size-3" />
                      {example.title}
                    </button>
                  ))}
                </div>
              </div>
            </>
          ) : null}

          {step === 1 && identification ? (
            <>
              <div className="border-line-soft bg-canvas/40 rounded-lg border p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="signal">{titleCase(identification.robot_type)}</Badge>
                  <span className="text-faint font-mono text-[10px]">
                    confidence {Math.round(identification.confidence * 100)}%
                  </span>
                </div>
                <p className="text-muted mt-2 text-xs leading-relaxed">
                  {identification.rationale}
                </p>
                {identification.key_requirements.length ? (
                  <ul className="mt-3 space-y-1">
                    {identification.key_requirements.map((item) => (
                      <li key={item} className="text-muted flex items-start gap-2 text-[11px]">
                        <CheckCircle2 className="text-signal/70 mt-0.5 size-3 shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>

              <Field>
                <Label htmlFor="robot-name">Robot name</Label>
                <Input
                  id="robot-name"
                  value={name}
                  onChange={(event) => setName(event.target.value.slice(0, 120))}
                  maxLength={120}
                />
              </Field>

              <div>
                <p className="text-ink/90 mb-2 text-[13px] font-medium">
                  Robot type — change it if we guessed wrong
                </p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {ROBOT_TYPES.map((option) => (
                    <OptionTile
                      key={option.value}
                      selected={robotType === option.value}
                      onClick={() => setRobotType(option.value)}
                      title={option.label}
                      description={option.description}
                      icon={<option.icon className="size-4" strokeWidth={1.6} />}
                    />
                  ))}
                </div>
              </div>
            </>
          ) : null}

          {step === 2 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {STORES.map((store) => (
                <OptionTile
                  key={store.value}
                  selected={shops.includes(store.value)}
                  onClick={() => setShops((current) => toggle(current, store.value))}
                  title={store.label}
                  description={store.blurb}
                  icon={<ShoppingCart className="size-3.5" />}
                />
              ))}
            </div>
          ) : null}

          {step === 3 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {CODE_LANGUAGES.map((language) => (
                <OptionTile
                  key={language.value}
                  selected={languages.includes(language.value)}
                  onClick={() => setLanguages((current) => toggle(current, language.value))}
                  title={language.label}
                  description={language.blurb}
                  icon={<Code2 className="size-3.5" />}
                />
              ))}
            </div>
          ) : null}

          {step === 4 ? (
            <>
              <div>
                <p className="text-ink/90 mb-2 text-[13px] font-medium">
                  Controller families{" "}
                  <span className="text-faint font-normal">(optional, pick all you own)</span>
                </p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {CONTROLLER_FAMILIES.map((controller) => (
                    <OptionTile
                      key={controller}
                      selected={controllers.includes(controller)}
                      onClick={() => setControllers((current) => toggle(current, controller))}
                      title={controller}
                      description={
                        controller === "ESP32"
                          ? "Wi-Fi + Bluetooth, recommended for rovers"
                          : controller === "Other"
                            ? "Describe it below"
                            : "Compatible with generated Arduino/C scaffolds"
                      }
                      icon={<Cpu className="size-3.5" />}
                    />
                  ))}
                </div>
              </div>

              <Field>
                <Label htmlFor="controller-notes">
                  Anything else about your hardware?{" "}
                  <span className="text-faint font-normal">(optional)</span>
                </Label>
                <Input
                  id="controller-notes"
                  value={controllerNotes}
                  onChange={(event) => setControllerNotes(event.target.value)}
                  placeholder="e.g. I have a spare L298N driver and a 2S LiPo"
                />
              </Field>

              <div>
                <p className="text-ink/90 mb-2 text-[13px] font-medium">
                  Do you want a custom PCB?
                </p>
                <div className="grid gap-2 sm:grid-cols-2">
                  <OptionTile
                    selected={!customPcb}
                    onClick={() => setCustomPcb(false)}
                    title="No — breadboard or off-the-shelf"
                    description="Recommended for a first build. Cheaper and faster to change."
                  />
                  <OptionTile
                    selected={customPcb}
                    onClick={() => setCustomPcb(true)}
                    title="Yes — design a custom PCB"
                    description="The build will reserve space for a board outline and mounting."
                  />
                </div>
              </div>
            </>
          ) : null}

          {step === 5 ? (
            <div className="space-y-4">
              <div className="border-line-soft bg-canvas/40 rounded-lg border p-4">
                <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
                  Your build
                </p>
                <p className="text-ink mt-1.5 text-lg font-medium">
                  {name || identification?.proposed_name || "Robot project"}
                </p>
                <p className="text-muted mt-1 text-xs leading-relaxed">{description}</p>
              </div>
              <dl className="grid gap-2 sm:grid-cols-2">
                {[
                  ["Robot type", selectedRobot.label],
                  ["Platform", titleCase(platform)],
                  [
                    "Stores",
                    shops.map((shop) => STORES.find((s) => s.value === shop)?.label).join(", "),
                  ],
                  [
                    "Languages",
                    languages
                      .map((language) => CODE_LANGUAGES.find((l) => l.value === language)?.label)
                      .join(", "),
                  ],
                  ["Controllers", controllers.join(", ") || "Planner chooses"],
                  ["Custom PCB", customPcb ? "Yes" : "No"],
                ].map(([label, value]) => (
                  <div
                    key={label}
                    className="border-line-soft bg-surface/60 rounded-lg border px-3 py-2.5"
                  >
                    <dt className="text-faint font-mono text-[8px] tracking-[0.14em] uppercase">
                      {label}
                    </dt>
                    <dd className="text-ink mt-1 text-xs leading-snug">{value}</dd>
                  </div>
                ))}
              </dl>
              <div className="border-signal/20 bg-signal/[0.05] rounded-lg border px-4 py-3">
                <p className="text-ink flex items-center gap-2 text-xs font-medium">
                  <CircuitBoard className="text-signal size-3.5" /> What gets generated
                </p>
                <ul className="text-muted mt-2 grid gap-1 text-[11px] sm:grid-cols-2">
                  <li>• Part prices at each store, cheapest first</li>
                  <li>• Electrical schematic, nets, and pinout</li>
                  <li>• Multi-file code for every language</li>
                  <li>• Reference STL, weight, and print price</li>
                  <li>• Budget roll-up in JOD</li>
                  <li>• Full documentation set</li>
                </ul>
              </div>
              {submitting ? (
                <div className="border-signal/20 bg-signal/[0.05] flex items-center gap-2.5 rounded-lg border px-4 py-3 text-xs">
                  <Loader2 className="text-signal size-4 animate-spin" />
                  <span className="text-ink">{progressLabel}</span>
                </div>
              ) : null}
            </div>
          ) : null}

          {error ? (
            <div className="border-danger/20 bg-danger/[0.06] text-danger flex items-start gap-2.5 rounded-lg border px-4 py-3 text-xs">
              <TriangleAlert className="mt-0.5 size-4 shrink-0" />
              <div>
                <p>{error}</p>
                <p className="text-danger/70 mt-1 text-[11px]">
                  Start the API with{" "}
                  <code className="bg-canvas/60 rounded px-1 py-0.5 font-mono">
                    cd apps/api &amp;&amp; uv run uvicorn app.main:app --reload
                  </code>
                </p>
              </div>
            </div>
          ) : null}

          <div className="border-line-soft flex flex-col-reverse items-stretch justify-between gap-3 border-t pt-4 sm:flex-row sm:items-center">
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setError(null);
                setStep((current) => Math.max(0, current - 1));
              }}
              disabled={step === 0 || submitting}
            >
              <ArrowLeft className="size-3.5" /> Back
            </Button>

            {step === 0 ? (
              <Button
                type="button"
                onClick={() => void identify()}
                disabled={!canContinue || identifying}
              >
                {identifying ? (
                  <>
                    <Loader2 className="size-4 animate-spin" /> Identifying…
                  </>
                ) : (
                  <>
                    Identify robot <ArrowRight className="size-4" />
                  </>
                )}
              </Button>
            ) : step < 5 ? (
              <Button
                type="button"
                onClick={() => {
                  setError(null);
                  setStep((current) => Math.min(5, current + 1));
                }}
                disabled={!canContinue}
              >
                Continue <ArrowRight className="size-4" />
              </Button>
            ) : (
              <Button type="button" onClick={() => void build()} disabled={submitting} size="lg">
                {submitting ? (
                  <>
                    <Loader2 className="size-4 animate-spin" /> Building…
                  </>
                ) : (
                  <>
                    <Sparkles className="size-4" /> Generate my build
                  </>
                )}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <p className="text-faint mt-4 text-center text-[11px]">
        Store prices are curated estimates in JOD, not live supplier quotes. Nothing is ordered.
      </p>
    </div>
  );
}
