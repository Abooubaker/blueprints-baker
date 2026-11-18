import {
  Armchair,
  Bot,
  CircleDot,
  CircuitBoard,
  Code2,
  Compass,
  Cpu,
  DollarSign,
  FileText,
  Gauge,
  Layers,
  Plane,
  Route,
  Ruler,
  Scan,
  Wrench,
  type LucideIcon,
} from "lucide-react";

import type { AgentName, CodeLanguage, RobotType, StoreName } from "@/lib/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
export const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH?.replace(/\/$/, "") ?? "";
export const DEMO_PROJECT_ID = "11111111-1111-4111-8111-111111111111";

export function assetPath(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${BASE_PATH}${normalized}`;
}

export interface RobotTypeOption {
  value: RobotType;
  label: string;
  description: string;
  icon: LucideIcon;
}

export const ROBOT_TYPES: RobotTypeOption[] = [
  {
    value: "line_follower",
    label: "Line follower",
    description: "Follows a marked path",
    icon: Route,
  },
  {
    value: "obstacle_avoider",
    label: "Obstacle avoider",
    description: "Navigates around objects",
    icon: Scan,
  },
  {
    value: "rover",
    label: "Rover",
    description: "Drives over varied terrain",
    icon: Compass,
  },
  {
    value: "robot_arm",
    label: "Robot arm",
    description: "Manipulates objects",
    icon: Armchair,
  },
  {
    value: "balancing_bot",
    label: "Balancing bot",
    description: "Stays upright on two wheels",
    icon: Gauge,
  },
  {
    value: "drone",
    label: "Drone",
    description: "Flies and stabilizes",
    icon: Plane,
  },
  {
    value: "custom",
    label: "Something else",
    description: "Describe your own idea",
    icon: Bot,
  },
];

export interface Capability {
  id: string;
  number: string;
  title: string;
  description: string;
  icon: LucideIcon;
  milestone: string;
  accent: "signal" | "aqua";
}

export const CAPABILITIES: Capability[] = [
  {
    id: "components",
    number: "01",
    title: "Component selection",
    description:
      "Turn a goal into a compatible bill of materials, with specs, availability, and price compared across trusted suppliers.",
    icon: Layers,
    milestone: "M4",
    accent: "signal",
  },
  {
    id: "electrical",
    number: "02",
    title: "Schematic assistant",
    description:
      "Get every pin and its destination, power budgets, and step-by-step wiring with electrical compatibility checks before anything is powered on.",
    icon: CircuitBoard,
    milestone: "M5",
    accent: "aqua",
  },
  {
    id: "programming",
    number: "03",
    title: "Code generation",
    description:
      "Generate firmware for Arduino, ESP32, or Raspberry Pi from the exact hardware configuration you selected.",
    icon: Cpu,
    milestone: "M6",
    accent: "signal",
  },
  {
    id: "mechanical",
    number: "04",
    title: "Mechanical design",
    description:
      "Plan the chassis, mounts, and drivetrain, then follow ordered assembly instructions with clear safety notes.",
    icon: Wrench,
    milestone: "M7",
    accent: "aqua",
  },
  {
    id: "cost",
    number: "05",
    title: "Cost estimation",
    description:
      "See a live total, a line-by-line breakdown, and budget alternatives so you can decide before you buy.",
    icon: DollarSign,
    milestone: "M8",
    accent: "signal",
  },
];

export interface AgentMeta {
  name: AgentName;
  label: string;
  short: string;
  icon: LucideIcon;
  dependsOn: AgentName[];
}

export const AGENTS: AgentMeta[] = [
  {
    name: "robot_planner",
    label: "Robot Planner",
    short: "Requirements → specification",
    icon: Bot,
    dependsOn: [],
  },
  {
    name: "component_research",
    label: "Component Research",
    short: "Specification → bill of materials",
    icon: Layers,
    dependsOn: ["robot_planner"],
  },
  {
    name: "electrical_engineering",
    label: "Electrical Engineering",
    short: "BOM → schematic and pinout",
    icon: CircuitBoard,
    dependsOn: ["robot_planner", "component_research"],
  },
  {
    name: "programming",
    label: "Programming",
    short: "Hardware → firmware bundle",
    icon: Cpu,
    dependsOn: ["robot_planner", "component_research", "electrical_engineering"],
  },
  {
    name: "mechanical_design",
    label: "Mechanical Design",
    short: "BOM → chassis and assembly",
    icon: Ruler,
    dependsOn: ["robot_planner", "component_research"],
  },
  {
    name: "cost_estimation",
    label: "Cost Estimation",
    short: "BOM → budget and alternatives",
    icon: CircleDot,
    dependsOn: ["robot_planner", "component_research"],
  },
];

export interface ProjectModule {
  slug: string;
  label: string;
  description: string;
  milestone: string;
  icon: LucideIcon;
  available: boolean;
}

export const PROJECT_MODULES: ProjectModule[] = [
  {
    slug: "components",
    label: "Parts & prices",
    description: "Every part priced at your selected stores, cheapest first.",
    milestone: "M4",
    icon: Layers,
    available: true,
  },
  {
    slug: "wiring",
    label: "Schematic & pinout",
    description: "Every pin and destination, power budget, validation, and KiCad exports.",
    milestone: "M5",
    icon: CircuitBoard,
    available: true,
  },
  {
    slug: "programming",
    label: "Code",
    description: "Multi-file code bundles with switchable languages.",
    milestone: "M6",
    icon: Code2,
    available: true,
  },
  {
    slug: "mechanical",
    label: "3D & print price",
    description: "Reference STL, weight, and the JOD material price chart.",
    milestone: "M7",
    icon: Wrench,
    available: true,
  },
  {
    slug: "cost",
    label: "Budget",
    description: "Line-item budget, print cost, and total project estimate.",
    milestone: "M8",
    icon: DollarSign,
    available: true,
  },
  {
    slug: "docs",
    label: "Documentation",
    description: "Sourcing, wiring, firmware, mechanical, safety, and decisions.",
    milestone: "M9",
    icon: FileText,
    available: true,
  },
];

export interface StoreOption {
  value: StoreName;
  label: string;
  blurb: string;
}

export const STORES: StoreOption[] = [
  { value: "temu", label: "Temu", blurb: "Lowest estimates, long shipping" },
  { value: "mikroelectron", label: "mikroelectron.com", blurb: "Local electronics parts" },
  { value: "waslleh", label: "waslleh.com", blurb: "Local hobby supplies" },
  { value: "amazon", label: "Amazon", blurb: "Fast, usually pricier" },
  { value: "aliexpress", label: "AliExpress", blurb: "Cheap modules, variable stock" },
  { value: "ghanimjo", label: "ghanimjo.com", blurb: "Local robotics supplier" },
];

export interface LanguageOption {
  value: CodeLanguage;
  label: string;
  blurb: string;
}

export const CODE_LANGUAGES: LanguageOption[] = [
  { value: "python", label: "Python", blurb: "MicroPython control loop" },
  { value: "cpp", label: "C++", blurb: "Arduino / PlatformIO" },
  { value: "c", label: "C", blurb: "STM32 HAL" },
  { value: "stm32_assembly", label: "STM32 assembly", blurb: "Cortex-M startup + loop" },
  { value: "verilog", label: "Verilog", blurb: "RTL scaffold with testbench" },
  { value: "vhdl", label: "VHDL", blurb: "RTL scaffold with testbench" },
  { value: "other", label: "Other", blurb: "Toolchain-neutral scaffold" },
];

export const CONTROLLER_FAMILIES = [
  "ESP32",
  "Arduino Uno",
  "Arduino Nano",
  "Raspberry Pi Pico",
  "STM32",
  "Teensy",
  "Other",
];

export const PRINT_CHART = [
  { material: "PLA", perGram: 0.07, base: 0.5, minimum: 1.0 },
  { material: "PETG", perGram: 0.12, base: 0.5, minimum: 1.2 },
  { material: "ABS", perGram: 0.12, base: 0.5, minimum: 1.0 },
  { material: "Resin", perGram: 0.3, base: 0.5, minimum: 1.5 },
  { material: "TPU", perGram: 0.2, base: 2.0, minimum: 1.2 },
] as const;

export const PROJECT_STATUS_STYLES: Record<
  string,
  { label: string; variant: "default" | "signal" | "aqua" | "warn" | "outline" }
> = {
  draft: { label: "Draft", variant: "default" },
  planning: { label: "Planning", variant: "aqua" },
  in_progress: { label: "In progress", variant: "signal" },
  ready: { label: "Ready", variant: "signal" },
  archived: { label: "Archived", variant: "outline" },
};

export const EXAMPLE_PROMPTS = [
  {
    title: "Classroom line follower",
    text: "A beginner-friendly line-following robot for a school science fair. It should follow a black tape track, stop when it detects an obstacle, and run for at least 30 minutes on AA batteries. Budget is around $60.",
  },
  {
    title: "Patio inspection rover",
    text: "A four-wheel rover that can drive on a concrete patio and stream a live camera feed to my phone. I want to control it over Wi-Fi, avoid collisions, and spend under $200.",
  },
  {
    title: "Desk robot arm",
    text: "A small 3-DOF robotic arm that can pick up a ping-pong ball and place it in a cup. I have an Arduino Uno already and would like to use servo motors. Budget under $120.",
  },
];
