"use client";

import { useCallback, useEffect, useState } from "react";

import { api, type User } from "@/lib/api";

export function useSession() {
  const [user, setUser] = useState<User | null>(null);
  const [checkingSession, setCheckingSession] = useState(true);

  useEffect(() => {
    let cancelled = false;

    api<User>("/auth/me/")
      .then((data) => {
        if (!cancelled) setUser(data);
      })
      .catch(() => {
        if (!cancelled) setUser(null);
      })
      .finally(() => {
        if (!cancelled) setCheckingSession(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const signOut = useCallback(async () => {
    try {
      await api("/auth/logout/", { method: "POST" });
    } catch {
      // The session is cleared locally even if the request fails.
    }
    setUser(null);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const data = await api<User>("/auth/me/");
      setUser(data);
      return data;
    } catch {
      return null;
    }
  }, []);

  return { user, checkingSession, signOut, refresh };
}
