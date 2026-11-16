"use client";

import { useCallback, useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api";
import type { ProjectSummary } from "@/lib/types";

interface ProjectsState {
  projects: ProjectSummary[];
  total: number;
  loading: boolean;
  error: string | null;
}

export function useProjects() {
  const [state, setState] = useState<ProjectsState>({
    projects: [],
    total: 0,
    loading: true,
    error: null,
  });
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    api
      .listProjects({ limit: 50 })
      .then((page) => {
        if (cancelled) return;
        setState({ projects: page.items, total: page.meta.total, loading: false, error: null });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          projects: [],
          total: 0,
          loading: false,
          error: error instanceof ApiError ? error.message : "Could not load projects.",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const reload = useCallback(() => {
    setState((current) => ({ ...current, loading: true, error: null }));
    setRefreshKey((key) => key + 1);
  }, []);

  return { ...state, reload };
}
