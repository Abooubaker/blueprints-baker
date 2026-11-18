import { API_BASE_URL, DEMO_MODE } from "@/lib/constants";
import {
  demoAgentCatalog,
  demoAgentRuns,
  demoBuild,
  demoElectrical,
  demoExportPath,
  demoOrchestration,
  demoProjectById,
  demoProjectSummaries,
  isDemoProject,
} from "@/lib/demo";
import type {
  AgentCatalog,
  AgentName,
  AgentRun,
  BuildArtifact,
  BuildPreferences,
  CreateProjectInput,
  ElectricalArtifact,
  ExportFormat,
  OrchestrationResult,
  Page,
  Project,
  ProjectSummary,
  RobotIdentification,
  RobotType,
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
      "Cannot reach the Blueprints Baker API. Is it running on " + API_BASE_URL + "?",
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
    if (DEMO_MODE) {
      const search = options?.search?.trim().toLowerCase();
      const items = demoProjectSummaries.filter(
        (project) =>
          (!search ||
            project.name.toLowerCase().includes(search) ||
            project.description.toLowerCase().includes(search)) &&
          (!options?.status || project.status === options.status) &&
          (!options?.robotType || project.robot_type === options.robotType),
      );
      return Promise.resolve({
        items,
        meta: { total: items.length, limit: options?.limit ?? 50, offset: options?.offset ?? 0 },
      });
    }
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
    if (DEMO_MODE) {
      const project = demoProjectById(id);
      return project
        ? Promise.resolve(project)
        : Promise.reject(new ApiError("This demo only contains one project.", "not_found", 404));
    }
    return request<Project>(`/api/v1/projects/${id}`);
  },

  createProject(payload: CreateProjectInput): Promise<Project> {
    if (DEMO_MODE) {
      return Promise.reject(
        new ApiError(
          "Project creation needs the full API. This Pages build is a read-only demo.",
          "demo_read_only",
          405,
        ),
      );
    }
    return request<Project>("/api/v1/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  runAgents(
    projectId: string,
    body: { agents?: AgentName[]; parameters?: Record<string, unknown> } = {},
  ): Promise<OrchestrationResult> {
    if (DEMO_MODE) {
      if (!isDemoProject(projectId)) {
        return Promise.reject(new ApiError("Demo project not found.", "not_found", 404));
      }
      return Promise.resolve({
        ...demoOrchestration,
        runs: body.agents
          ? demoOrchestration.runs.filter((run) => body.agents?.includes(run.agent))
          : demoOrchestration.runs,
      });
    }
    return request<OrchestrationResult>(`/api/v1/projects/${projectId}/agent-runs`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getAgentCatalog(): Promise<AgentCatalog> {
    if (DEMO_MODE) return Promise.resolve(demoAgentCatalog);
    return request<AgentCatalog>("/api/v1/agents");
  },

  listAgentRuns(
    projectId: string,
    options?: { limit?: number; offset?: number },
  ): Promise<Page<AgentRun>> {
    if (DEMO_MODE) {
      const items = demoAgentRuns.slice(
        options?.offset ?? 0,
        (options?.offset ?? 0) + (options?.limit ?? 50),
      );
      return Promise.resolve({
        items,
        meta: {
          total: demoAgentRuns.length,
          limit: options?.limit ?? 50,
          offset: options?.offset ?? 0,
        },
      });
    }
    const params = new URLSearchParams();
    if (options?.limit) params.set("limit", String(options.limit));
    if (options?.offset) params.set("offset", String(options.offset));
    const query = params.toString();
    return request<Page<AgentRun>>(
      `/api/v1/projects/${projectId}/agent-runs${query ? `?${query}` : ""}`,
    );
  },

  generateElectrical(projectId: string): Promise<ElectricalArtifact> {
    if (DEMO_MODE) {
      if (!isDemoProject(projectId)) {
        return Promise.reject(new ApiError("Demo project not found.", "not_found", 404));
      }
      return Promise.resolve(demoElectrical);
    }
    return request<ElectricalArtifact>(`/api/v1/projects/${projectId}/electrical`, {
      method: "POST",
    });
  },

  getElectrical(projectId: string): Promise<ElectricalArtifact> {
    if (DEMO_MODE) {
      if (!isDemoProject(projectId)) {
        return Promise.reject(new ApiError("Demo project not found.", "not_found", 404));
      }
      return Promise.resolve(demoElectrical);
    }
    return request<ElectricalArtifact>(`/api/v1/projects/${projectId}/electrical`);
  },

  exportUrl(projectId: string, format: ExportFormat): string {
    if (DEMO_MODE) return demoExportPath(format);
    return `${API_BASE_URL}/api/v1/projects/${projectId}/electrical/export/${format}`;
  },

  identifyRobot(description: string, robotType?: RobotType): Promise<RobotIdentification> {
    if (DEMO_MODE) {
      return Promise.reject(
        new ApiError(
          "Robot identification needs the full API. This Pages build is a read-only demo.",
          "demo_read_only",
          405,
        ),
      );
    }
    return request<RobotIdentification>("/api/v1/intent/identify", {
      method: "POST",
      body: JSON.stringify({ description, robot_type: robotType ?? null }),
    });
  },

  getPreferences(projectId: string): Promise<BuildPreferences> {
    if (DEMO_MODE) {
      if (!isDemoProject(projectId)) {
        return Promise.reject(new ApiError("Demo project not found.", "not_found", 404));
      }
      return Promise.resolve(demoBuild.preferences);
    }
    return request<BuildPreferences>(`/api/v1/projects/${projectId}/preferences`);
  },

  savePreferences(projectId: string, preferences: BuildPreferences): Promise<BuildPreferences> {
    if (DEMO_MODE) {
      return Promise.reject(
        new ApiError(
          "Saving guided answers needs the full API. This Pages build is read-only.",
          "demo_read_only",
          405,
        ),
      );
    }
    return request<BuildPreferences>(`/api/v1/projects/${projectId}/preferences`, {
      method: "PUT",
      body: JSON.stringify(preferences),
    });
  },

  generateBuild(projectId: string): Promise<BuildArtifact> {
    if (DEMO_MODE) {
      if (!isDemoProject(projectId)) {
        return Promise.reject(new ApiError("Demo project not found.", "not_found", 404));
      }
      return Promise.resolve(demoBuild);
    }
    return request<BuildArtifact>(`/api/v1/projects/${projectId}/build`, { method: "POST" });
  },

  getBuild(projectId: string): Promise<BuildArtifact> {
    if (DEMO_MODE) {
      if (!isDemoProject(projectId)) {
        return Promise.reject(new ApiError("Demo project not found.", "not_found", 404));
      }
      return Promise.resolve(demoBuild);
    }
    return request<BuildArtifact>(`/api/v1/projects/${projectId}/build`);
  },
};
