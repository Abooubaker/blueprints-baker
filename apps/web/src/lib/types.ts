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
