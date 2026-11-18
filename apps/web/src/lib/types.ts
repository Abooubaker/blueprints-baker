export type ProjectStatus = "draft" | "planning" | "in_progress" | "ready" | "archived";
export type RobotType =
  | "line_follower"
  | "obstacle_avoider"
  | "rover"
  | "robot_arm"
  | "drone"
  | "balancing_bot"
  | "custom";
export type Difficulty = "beginner" | "intermediate" | "advanced";
export type TargetPlatform = "arduino" | "esp32" | "raspberry_pi" | "other" | "undecided";
export type DriveType = "differential" | "mecanum" | "omni" | "tank" | "servo_arm" | "none";
export type AgentName =
  | "robot_planner"
  | "component_research"
  | "electrical_engineering"
  | "programming"
  | "mechanical_design"
  | "cost_estimation";
export type AgentRunStatus =
  "queued" | "running" | "succeeded" | "failed" | "cancelled" | "skipped" | "not_implemented";
export type AgentResultStatus = "succeeded" | "failed" | "skipped" | "not_implemented";

export interface PageMeta {
  total: number;
  limit: number;
  offset: number;
}

export interface Page<T> {
  items: T[];
  meta: PageMeta;
}

export interface RobotSpecification {
  id: string;
  project_id: string;
  summary?: string;
  use_case?: string;
  environment?: string;
  target_platform?: TargetPlatform;
  drive_type?: DriveType;
  power_source?: string;
  payload_capacity_kg?: number | null;
  dimensions?: Record<string, number | null>;
  requirements?: string[];
  constraints?: string[];
  status: "draft" | "generated" | "approved";
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  slug: string;
  description: string;
  robot_type: RobotType;
  status: ProjectStatus;
  difficulty: Difficulty;
  budget_max_usd: number | null;
  created_at: string;
  updated_at: string;
}

export interface Project extends ProjectSummary {
  owner_id: string | null;
  budget_min_usd: number | null;
  specification: RobotSpecification | null;
}

export interface CreateProjectInput {
  name: string;
  description?: string;
  robot_type?: RobotType;
  difficulty?: Difficulty;
  target_platform?: TargetPlatform;
  budget_min_usd?: number | null;
  budget_max_usd?: number | null;
  requirements?: string[];
  constraints?: string[];
}

export interface AgentDescriptor {
  name: AgentName;
  display_name: string;
  description: string;
  status: "placeholder" | "available";
  depends_on: AgentName[];
  input_schema: string;
  output_schema: string;
  milestone: string;
  owner_area: string;
}

export interface AgentCatalog {
  provider: string;
  model: string;
  agents: AgentDescriptor[];
}

export interface AgentRun {
  id: string;
  project_id: string;
  agent: AgentName;
  status: AgentRunStatus;
  provider: string;
  model: string;
  summary?: string;
  output_payload: Record<string, unknown> | null;
  error_message: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  latency_ms: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface OrchestrationResult {
  project_id: string;
  status: AgentResultStatus;
  runs: AgentRun[];
  shared_context: Record<string, unknown>;
  provider: string;
  model: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
    request_id?: string;
  };
}

export type ConnectionKind = "power" | "ground" | "signal" | "motor" | "bus";
export type IssueSeverity = "error" | "warning" | "info";

export interface ElectricalNodePin {
  name: string;
  kind: string;
  voltage_v: number | null;
  connected: boolean;
}

export interface ElectricalNode {
  ref: string;
  label: string;
  kind: "controller" | "motor" | "driver" | "sensor" | "power" | "actuator" | "regulator" | "other";
  role: string;
  library_key: string;
  voltage_v: number | null;
  current_ma: number | null;
  peak_current_ma: number | null;
  pins: ElectricalNodePin[];
  notes: string;
}

export interface ElectricalConnection {
  from_ref: string;
  from_pin: string;
  to_ref: string;
  to_pin: string;
  net: string;
  signal: string;
  kind: ConnectionKind;
  voltage_v: number | null;
  wire_color: string;
  wire_gauge_awg: number | null;
  connector: string;
  notes: string;
}

export interface PinDestination {
  ref: string;
  pin: string;
  net: string;
  signal: string;
  kind: ConnectionKind;
  connector: string;
}

export interface ElectricalPinoutEntry {
  ref: string;
  part: string;
  role: string;
  pin: string;
  pin_kind: string;
  voltage_v: number | null;
  net: string;
  signal: string;
  connected: boolean;
  destinations: PinDestination[];
  wire_color: string;
  wire_gauge_awg: number | null;
}

export interface ElectricalIssue {
  code: string;
  severity: IssueSeverity;
  message: string;
  refs: string[];
  remediation: string;
}

export interface PowerRail {
  name: string;
  voltage_v: number | null;
  peak_current_ma: number | null;
  source_ref: string;
  notes: string;
}

export interface PowerBudget {
  supply_voltage_v: number | null;
  peak_current_ma: number | null;
  typical_current_ma: number | null;
  recommended_supply_ma: number | null;
  margin_percent: number | null;
  usable_capacity_mah: number | null;
  estimated_runtime_min: number | null;
}

export interface ElectricalPlan {
  nodes: ElectricalNode[];
  connections: ElectricalConnection[];
  pinout: ElectricalPinoutEntry[];
  power_budget: PowerBudget;
  power_rails: PowerRail[];
  pin_map: Record<string, string>;
  issues: ElectricalIssue[];
  safety_checks: string[];
  warnings: string[];
  wiring_steps: string[];
  design_notes: string[];
  library_version: string;
}

export interface ComponentCandidate {
  name: string;
  manufacturer: string;
  model_number: string;
  category: string;
  specs: Record<string, unknown>;
  price_usd: number | string | null;
  supplier: string;
  supplier_url: string | null;
  availability: string;
  compatibility_notes: string[];
  score: number;
}

export interface BomItem {
  role: string;
  category: string;
  quantity: number;
  required: boolean;
  selection: ComponentCandidate | null;
  rationale: string;
}

export interface ComponentResearchOutput {
  bill_of_materials: BomItem[];
  unresolved_requirements: string[];
  compatibility_notes: string[];
  total_estimated_usd: number | string | null;
  sources: string[];
}

export type ExportFormat =
  | "json"
  | "wiring-csv"
  | "pinout-csv"
  | "bom-csv"
  | "kicad-netlist"
  | "kicad-schematic"
  | "svg"
  | "markdown";

export interface ExportFormatDescriptor {
  format: ExportFormat;
  label: string;
  filename: string;
  media_type: string;
  description: string;
}

export interface ElectricalArtifact {
  project_id: string;
  project_name: string;
  agent_run_id: string;
  generated_at: string;
  plan: ElectricalPlan;
  bom: ComponentResearchOutput | null;
  total_estimated_usd: number | null;
  export_formats: ExportFormatDescriptor[];
}
