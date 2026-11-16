import { API_BASE_URL } from "@/lib/constants";
import type {
  AgentCatalog,
  AgentName,
  AgentRun,
  CreateProjectInput,
  OrchestrationResult,
  Page,
  Project,
  ProjectSummary,
} from "@/lib/types";

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details?: unknown;

  constructor(message: string, code = "request_failed", status = 0, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      "Cannot reach the RoboCraft API. Is it running on " + API_BASE_URL + "?",
      "network_error",
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const body = (await response.json().catch(() => null)) as {
    error?: { code?: string; message?: string; details?: unknown };
  } | null;

  if (!response.ok) {
    throw new ApiError(
      body?.error?.message ?? `Request failed with status ${response.status}`,
      body?.error?.code ?? "request_failed",
      response.status,
      body?.error?.details,
    );
  }

  return body as T;
}

export const api = {
  listProjects(options?: {
    limit?: number;
    offset?: number;
    status?: string;
    robotType?: string;
    search?: string;
  }): Promise<Page<ProjectSummary>> {
    const params = new URLSearchParams();
    if (options?.limit) params.set("limit", String(options.limit));
    if (options?.offset) params.set("offset", String(options.offset));
    if (options?.status) params.set("status", options.status);
    if (options?.robotType) params.set("robot_type", options.robotType);
    if (options?.search) params.set("search", options.search);
    const query = params.toString();
    return request<Page<ProjectSummary>>(`/api/v1/projects${query ? `?${query}` : ""}`);
  },

  getProject(id: string): Promise<Project> {
    return request<Project>(`/api/v1/projects/${id}`);
  },

  createProject(payload: CreateProjectInput): Promise<Project> {
    return request<Project>("/api/v1/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  runAgents(
    projectId: string,
    body: { agents?: AgentName[]; parameters?: Record<string, unknown> } = {},
  ): Promise<OrchestrationResult> {
    return request<OrchestrationResult>(`/api/v1/projects/${projectId}/agent-runs`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getAgentCatalog(): Promise<AgentCatalog> {
    return request<AgentCatalog>("/api/v1/agents");
  },

  listAgentRuns(
    projectId: string,
    options?: { limit?: number; offset?: number },
  ): Promise<Page<AgentRun>> {
    const params = new URLSearchParams();
    if (options?.limit) params.set("limit", String(options.limit));
    if (options?.offset) params.set("offset", String(options.offset));
    const query = params.toString();
    return request<Page<AgentRun>>(
      `/api/v1/projects/${projectId}/agent-runs${query ? `?${query}` : ""}`,
    );
  },
};
