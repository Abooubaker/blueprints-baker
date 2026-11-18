"use client";

import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api";
import type { BuildArtifact } from "@/lib/types";

export function useBuild(projectId: string) {
  const [build, setBuild] = useState<BuildArtifact | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getBuild(projectId)
      .then((result) => {
        if (cancelled) return;
        setBuild(result);
        setError(null);
      })
      .catch((caught: unknown) => {
        if (cancelled) return;
        setError(
          caught instanceof ApiError ? caught.message : "Could not load the generated build.",
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  return { build, loading, error, setBuild };
}
