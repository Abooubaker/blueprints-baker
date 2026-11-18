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

export type StoreName = "temu" | "mikroelectron" | "waslleh" | "amazon" | "aliexpress" | "ghanimjo";

export type CodeLanguage = "python" | "cpp" | "c" | "stm32_assembly" | "verilog" | "vhdl" | "other";

export type PrintMaterial = "PLA" | "PETG" | "ABS" | "Resin" | "TPU";

export interface StoreOffer {
  store: StoreName;
  label: string;
  price_jod: number | string;
  product_url: string;
  availability: string;
  is_estimate: boolean;
  note: string;
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
  offers?: StoreOffer[];
  cheapest_store?: StoreName | null;
  cheapest_price_jod?: number | string | null;
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
  total_estimated_jod?: number | string | null;
  selected_shops?: StoreName[];
  currency?: string;
  sources: string[];
}

export interface RobotIdentification {
  proposed_name: string;
  robot_type: RobotType;
  confidence: number;
  rationale: string;
  suggested_platform: TargetPlatform;
  suggested_difficulty: Difficulty;
  key_requirements: string[];
  needs_confirmation: boolean;
}

export interface PrintSettings {
  material: PrintMaterial;
  infill_percent: number;
  price_per_gram_jod: number | string | null;
}

export interface BuildPreferences {
  description: string;
  robot_name: string;
  robot_type: RobotType;
  difficulty: Difficulty;
  shops: StoreName[];
  languages: CodeLanguage[];
  controllers: string[];
  controller_notes: string;
  custom_pcb: boolean;
  confirmed: boolean;
  budget_max_usd: number | string | null;
  identification_rationale: string;
  identification_confidence: number;
  print_settings: PrintSettings;
}

export interface CodeFile {
  path: string;
  language: string;
  content: string;
  explanation: string;
}

export interface LanguageBundle {
  language: CodeLanguage;
  display_name: string;
  framework: string;
  status: "complete" | "scaffold";
  files: CodeFile[];
  libraries: string[];
  notes: string[];
}

export interface ProgrammingOutput {
  platform: TargetPlatform;
  language: string;
  framework: string;
  files: CodeFile[];
  bundles: LanguageBundle[];
  libraries: string[];
  pin_assignments: Record<string, string>;
  setup_steps: string[];
  upload_steps: string[];
  validation_notes: string[];
}

export interface PrintMaterialQuote {
  material: PrintMaterial;
  price_per_gram_jod: number | string;
  base_jod: number | string;
  minimum_jod: number | string;
  weight_g: number | string;
  total_jod: number | string;
  is_cheapest: boolean;
  is_selected: boolean;
}

export interface MechanicalPart {
  name: string;
  category: string;
  quantity: number;
  material: string;
  dimensions_mm?: Record<string, number | null>;
  notes: string;
}

export interface AssemblyStep {
  order: number;
  title: string;
  instructions: string;
  tools: string[];
  parts: string[];
  safety_notes: string[];
}

export interface MechanicalOutput {
  chassis: MechanicalPart | null;
  parts: MechanicalPart[];
  assembly_steps: AssemblyStep[];
  drawings: string[];
  manufacturing_notes: string[];
  warnings: string[];
  dimensions_mm: { length_mm: number | null; width_mm: number | null; height_mm: number | null };
  volume_cm3: number | string;
  infill_percent: number;
  material_fraction: number | string;
  selected_material: PrintMaterial;
  custom_price_per_gram_jod: number | string | null;
  print_price_jod: number | string | null;
  stl_ascii: string;
  stl_filename: string;
  material_quotes: PrintMaterialQuote[];
  pricing_notes: string[];
}

export interface CostLineItem {
  label: string;
  category: string;
  quantity: number;
  unit_price_usd: number | string | null;
  line_total_usd: number | string | null;
  unit_price_jod?: number | string | null;
  line_total_jod?: number | string | null;
  supplier: string;
  is_estimate: boolean;
}

export interface BudgetAlternative {
  description: string;
  savings_usd: number | string | null;
  tradeoffs: string[];
}

export interface CostEstimate {
  line_items: CostLineItem[];
  subtotal_usd: number | string | null;
  subtotal_jod: number | string | null;
  shipping_usd: number | string | null;
  contingency_usd: number | string | null;
  print_cost_jod: number | string | null;
  total_usd: number | string | null;
  total_jod: number | string | null;
  currency: string;
  budget: { min_usd: number | string | null; max_usd: number | string | null; currency: string };
  budget_status: "under" | "within" | "over" | "unknown";
  alternatives: BudgetAlternative[];
  assumptions: string[];
}

export interface DocumentationFile {
  path: string;
  title: string;
  content: string;
}

export interface ProjectDocumentation {
  files: DocumentationFile[];
  summary: string;
  notes: string[];
}

export interface BuildArtifact {
  project_id: string;
  project_name: string;
  status: "ready" | "partial" | "empty";
  generated_at: string;
  preferences: BuildPreferences;
  identification: RobotIdentification | null;
  specification: RobotSpecificationDraft | null;
  research: ComponentResearchOutput | null;
  electrical: ElectricalPlan | null;
  programming: ProgrammingOutput | null;
  mechanical: MechanicalOutput | null;
  cost: CostEstimate | null;
  documentation: ProjectDocumentation;
  missing: string[];
  warnings: string[];
}

export interface RobotSpecificationDraft {
  summary: string;
  use_case: string;
  robot_type: RobotType;
  difficulty: Difficulty;
  target_platform: TargetPlatform;
  drive_type: DriveType;
  environment: string;
  power_source: string;
  dimensions: { length_mm: number | null; width_mm: number | null; height_mm: number | null };
  payload_capacity_kg: number | string | null;
  requirements: string[];
  constraints: string[];
  success_criteria: string[];
  open_questions: string[];
  confidence: number;
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
