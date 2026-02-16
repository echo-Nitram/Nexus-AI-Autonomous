"use client";

import { useState, useEffect, useCallback } from "react";

const DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001";

export function useUserId(): string {
  if (typeof window !== "undefined") {
    return localStorage.getItem("nexus_user_id") || DEFAULT_USER_ID;
  }
  return DEFAULT_USER_ID;
}

export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
): { data: T | null; loading: boolean; error: string | null; refetch: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    setError(null);
    fetcher()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}
