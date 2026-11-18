"use client";

import {
  ArrowRight,
  BrainCircuit,
  Check,
  ChevronDown,
  Info,
  Loader2,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldError, FieldHint, Input, Label, Select, Textarea } from "@/components/ui/form";
import { Separator } from "@/components/ui/misc";
import { api, ApiError } from "@/lib/api";
import { EXAMPLE_PROMPTS, ROBOT_TYPES } from "@/lib/constants";
import type { Difficulty, RobotType, TargetPlatform } from "@/lib/types";
import { cn, formatMoney, titleCase } from "@/lib/utils";

const MAX_DESCRIPTION = 2000;

export function CreateProjectForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [robotType, setRobotType] = useState<RobotType>("line_follower");
  const [platform, setPlatform] = useState<TargetPlatform>("undecided");
  const [difficulty, setDifficulty] = useState<Difficulty>("beginner");
  const [budgetMin, setBudgetMin] = useState("");
  const [budgetMax, setBudgetMax] = useState("");
  const [requirements, setRequirements] = useState("");
  const [constraints, setConstraints] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  const selectedRobot = ROBOT_TYPES.find((item) => item.value === robotType) ?? ROBOT_TYPES[0]!;

  function applyExample(text: string, index: number) {
    setDescription(text);
    if (!name) setName(EXAMPLE_PROMPTS[index]?.title ?? "");
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const errors: Record<string, string> = {};
    if (!name.trim()) errors.name = "Give your project a name.";
    if (description.trim().length < 20) {
      errors.description =
        "Describe the robot in at least 20 characters so the planner has context.";
    }
    const min = budgetMin ? Number(budgetMin) : null;
    const max = budgetMax ? Number(budgetMax) : null;
    if (min !== null && max !== null && max < min) {
      errors.budget = "The maximum budget cannot be lower than the minimum.";
    }
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      const project = await api.createProject({
        name: name.trim(),
        description: description.trim(),
        robot_type: robotType,
        target_platform: platform,
        difficulty,
        budget_min_usd: min,
        budget_max_usd: max,
        requirements: requirements
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean),
        constraints: constraints
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean),
      });
      router.push(`/projects/${project.id}`);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not create the project. Check that the API is running.",
      );
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="grid items-start gap-6 xl:grid-cols-[1fr_340px]">
      <div className="space-y-5">
        <Card>
          <CardHeader>
            <CardTitle>Project basics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <Field>
              <Label htmlFor="name">
                Project name <span className="text-danger">*</span>
              </Label>
              <Input
                id="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="e.g. Science fair line follower"
                maxLength={120}
                autoFocus
                aria-invalid={Boolean(fieldErrors.name)}
              />
              <FieldError>{fieldErrors.name}</FieldError>
            </Field>

            <Field>
              <div className="flex items-center justify-between">
                <Label htmlFor="description">
                  Describe the robot you want to build <span className="text-danger">*</span>
                </Label>
                <span className="text-faint font-mono text-[10px]">
                  {description.length}/{MAX_DESCRIPTION}
                </span>
              </div>
              <Textarea
                id="description"
                value={description}
                onChange={(event) => setDescription(event.target.value.slice(0, MAX_DESCRIPTION))}
                placeholder="What should it do? Where will it operate? What is your budget, experience level, and any hardware you already own?"
                className="min-h-36"
                aria-invalid={Boolean(fieldErrors.description)}
              />
              {fieldErrors.description ? (
                <FieldError>{fieldErrors.description}</FieldError>
              ) : (
                <FieldHint>
                  Be concrete about the goal, environment, and constraints. The Planner will turn
                  this into a structured specification.
                </FieldHint>
              )}
            </Field>

            <div>
              <p className="text-faint mb-2 text-[11px]">Need a starting point?</p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLE_PROMPTS.map((example, index) => (
                  <button
                    key={example.title}
                    type="button"
                    onClick={() => applyExample(example.text, index)}
                    className="border-line bg-canvas/50 text-muted hover:border-signal/30 hover:text-ink flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[11px] transition-colors"
                  >
                    <Sparkles className="text-signal/70 size-3" />
                    {example.title}
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Robot type</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {ROBOT_TYPES.map((option) => {
                const selected = option.value === robotType;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setRobotType(option.value)}
                    aria-pressed={selected}
                    className={cn(
                      "flex flex-col items-start rounded-lg border px-3 py-3 text-left transition-colors",
                      selected
                        ? "border-signal/40 bg-signal/[0.07]"
                        : "border-line bg-canvas/40 hover:border-[#2d6894]",
                    )}
                  >
                    <div className="flex w-full items-center justify-between">
                      <option.icon
                        className={cn("size-4", selected ? "text-signal" : "text-faint")}
                        strokeWidth={1.7}
                      />
                      {selected ? (
                        <span className="bg-signal text-signal-ink flex size-4 items-center justify-center rounded-full">
                          <Check className="size-2.5" strokeWidth={3} />
                        </span>
                      ) : null}
                    </div>
                    <span
                      className={cn(
                        "mt-2.5 text-[12px] font-medium",
                        selected ? "text-ink" : "text-muted",
                      )}
                    >
                      {option.label}
                    </span>
                    <span className="text-faint mt-0.5 text-[10px] leading-snug">
                      {option.description}
                    </span>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Build constraints</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-3">
              <Field>
                <Label htmlFor="platform">Target platform</Label>
                <Select
                  id="platform"
                  value={platform}
                  onChange={(event) => setPlatform(event.target.value as TargetPlatform)}
                >
                  <option value="undecided">Decide for me</option>
                  <option value="arduino">Arduino</option>
                  <option value="esp32">ESP32</option>
                  <option value="raspberry_pi">Raspberry Pi</option>
                  <option value="other">Other</option>
                </Select>
              </Field>

              <Field>
                <Label htmlFor="difficulty">Experience level</Label>
                <Select
                  id="difficulty"
                  value={difficulty}
                  onChange={(event) => setDifficulty(event.target.value as Difficulty)}
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </Select>
              </Field>

              <Field>
                <Label>Budget range (USD)</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    inputMode="decimal"
                    min={0}
                    step={1}
                    value={budgetMin}
                    onChange={(event) => setBudgetMin(event.target.value)}
                    placeholder="Min"
                    aria-label="Minimum budget in USD"
                    className="h-11"
                  />
                  <span className="text-faint">–</span>
                  <Input
                    type="number"
                    inputMode="decimal"
                    min={0}
                    step={1}
                    value={budgetMax}
                    onChange={(event) => setBudgetMax(event.target.value)}
                    placeholder="Max"
                    aria-label="Maximum budget in USD"
                    className="h-11"
                  />
                </div>
                {fieldErrors.budget ? <FieldError>{fieldErrors.budget}</FieldError> : null}
              </Field>
            </div>

            <details className="group border-line-soft bg-canvas/30 rounded-lg border">
              <summary className="text-muted hover:text-ink flex cursor-pointer items-center justify-between px-4 py-3 text-xs select-none">
                <span className="flex items-center gap-2">
                  <ChevronDown className="size-3.5 transition-transform group-open:rotate-180" />
                  Add detailed requirements and constraints
                </span>
                <span className="text-faint font-mono text-[9px] tracking-wider uppercase">
                  optional
                </span>
              </summary>
              <Separator />
              <div className="grid gap-4 p-4 sm:grid-cols-2">
                <Field>
                  <Label htmlFor="requirements">Requirements</Label>
                  <Textarea
                    id="requirements"
                    value={requirements}
                    onChange={(event) => setRequirements(event.target.value)}
                    placeholder={"One per line\nFollow a black line\nStop at obstacles"}
                    className="min-h-24 text-xs"
                  />
                </Field>
                <Field>
                  <Label htmlFor="constraints">Constraints</Label>
                  <Textarea
                    id="constraints"
                    value={constraints}
                    onChange={(event) => setConstraints(event.target.value)}
                    placeholder={"One per line\nMust run on AA batteries\nUnder $60"}
                    className="min-h-24 text-xs"
                  />
                </Field>
              </div>
            </details>
          </CardContent>
        </Card>

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

        <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
          <p className="text-faint text-[11px]">
            A draft project and specification are created. No AI provider calls are made.
          </p>
          <Button type="submit" size="lg" disabled={submitting}>
            {submitting ? (
              <>
                <Loader2 className="size-4 animate-spin" /> Creating project…
              </>
            ) : (
              <>
                Create project <ArrowRight className="size-4" />
              </>
            )}
          </Button>
        </div>
      </div>

      <aside className="space-y-4 xl:sticky xl:top-24">
        <Card className="panel-sheen">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Specification preview</CardTitle>
              <Badge variant="outline">draft</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="border-signal/25 bg-signal/10 text-signal flex size-10 items-center justify-center rounded-lg border">
                <selectedRobot.icon className="size-4.5" />
              </div>
              <div className="min-w-0">
                <p className="text-ink truncate text-[13px] font-medium">
                  {name || "Untitled robot"}
                </p>
                <p className="text-faint text-[10px]">{selectedRobot.label}</p>
              </div>
            </div>

            <Separator />

            <dl className="space-y-2.5 text-[12px]">
              {[
                ["Platform", platform === "undecided" ? "Planner decides" : titleCase(platform)],
                ["Difficulty", titleCase(difficulty)],
                [
                  "Budget",
                  budgetMax
                    ? `${budgetMin ? `${formatMoney(Number(budgetMin))} – ` : "Up to "}${formatMoney(Number(budgetMax))}`
                    : "Not set",
                ],
                ["Requirements", requirements.split("\n").filter(Boolean).length || "—"],
                ["Constraints", constraints.split("\n").filter(Boolean).length || "—"],
              ].map(([label, value]) => (
                <div key={label} className="flex items-center justify-between gap-3">
                  <dt className="text-faint">{label}</dt>
                  <dd className="text-muted truncate text-right">{value}</dd>
                </div>
              ))}
            </dl>

            <div className="border-line-soft bg-canvas/40 rounded-lg border p-3">
              <div className="text-aqua flex items-center gap-1.5 text-[10px] font-medium">
                <Info className="size-3" /> What happens next
              </div>
              <ol className="text-faint mt-2 space-y-1.5 text-[10px] leading-relaxed">
                <li>1. The project and draft spec are saved.</li>
                <li>2. You review the overview and module map.</li>
                <li>3. Planner execution arrives in milestone M3.</li>
              </ol>
            </div>
          </CardContent>
        </Card>

        <div className="rounded-panel border-line-soft bg-surface/60 flex items-start gap-2.5 border px-4 py-3">
          <BrainCircuit className="text-signal/70 mt-0.5 size-4 shrink-0" />
          <p className="text-faint text-[11px] leading-relaxed">
            Specialized AI agents are placeholder services in this foundation release. The API
            records every run without pretending an unimplemented agent succeeded.
          </p>
        </div>
      </aside>
    </form>
  );
}
