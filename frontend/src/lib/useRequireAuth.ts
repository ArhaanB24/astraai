"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./AuthContext";

export function useRequireAuth(options?: { requireOnboarding?: boolean }) {
  const { user, token, isLoading } = useAuth();
  const router = useRouter();
  const requireOnboarding = options?.requireOnboarding ?? true;

  useEffect(() => {
    if (!isLoading) {
      if (!token || !user) {
        router.replace("/login");
      } else if (requireOnboarding && !user.onboarding_completed) {
        router.replace("/onboarding");
      }
    }
  }, [user, token, isLoading, router, requireOnboarding]);

  return { user, token, isLoading, isAuthenticated: Boolean(token && user) };
}
