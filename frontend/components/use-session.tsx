"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import { api, type User } from "@/lib/api";

type SessionContextValue = {
  user: User | null;
  checkingSession: boolean;
  signingOut: boolean;
  signOut: () => Promise<void>;
  refresh: () => Promise<User | null>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

/**
 * One session for the whole app. /auth/me/ is fetched once, when this
 * provider mounts on a page load. Client-side navigation between pages reuses
 * the same state; sign-in, sign-out and an explicit refresh are the only other
 * things that call the API.
 */
export function SessionProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [signingOut, setSigningOut] = useState(false);

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

  const refresh = useCallback(async () => {
    try {
      const data = await api<User>("/auth/me/");
      setUser(data);
      return data;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  const signOut = useCallback(async () => {
    if (signingOut) return;
    setSigningOut(true);
    try {
      await api("/auth/logout/", { method: "POST" });
    } catch {
      // Clear the local session even if the request fails.
    }
    setUser(null);
    router.replace("/");
    router.refresh();
    setSigningOut(false);
  }, [router, signingOut]);

  const value = useMemo(
    () => ({ user, checkingSession, signingOut, signOut, refresh }),
    [user, checkingSession, signingOut, signOut, refresh],
  );

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used inside a SessionProvider");
  }
  return context;
}
