"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active?: boolean;
  onboarding_completed?: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<User | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const getApiBase = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== "undefined") {
    return "/api/v1";
  }
  return "http://localhost:8000/api/v1";
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const refreshUser = async (): Promise<User | null> => {
    try {
      const currentToken = token || localStorage.getItem("arthaai_token");
      if (!currentToken) return null;

      const res = await fetch(`${getApiBase()}/auth/me`, {
        headers: { Authorization: `Bearer ${currentToken}` },
      });
      if (res.ok) {
        const freshUser: User = await res.json();
        setUser(freshUser);
        localStorage.setItem("arthaai_user", JSON.stringify(freshUser));
        return freshUser;
      }
    } catch {}
    return null;
  };

  useEffect(() => {
    // Check saved session on client mount
    try {
      const savedToken = localStorage.getItem("arthaai_token");
      const savedUser = localStorage.getItem("arthaai_user");

      if (savedToken && savedUser) {
        setToken(savedToken);
        const parsed = JSON.parse(savedUser);
        setUser(parsed);
        // Refresh asynchronously to ensure onboarding_completed is up to date
        fetch(`${getApiBase()}/auth/me`, {
          headers: { Authorization: `Bearer ${savedToken}` },
        })
          .then((res) => (res.ok ? res.json() : null))
          .then((fresh) => {
            if (fresh) {
              setUser(fresh);
              localStorage.setItem("arthaai_user", JSON.stringify(fresh));
            }
          })
          .catch(() => {});
      } else {
        setToken(null);
        setUser(null);
      }
    } catch (e) {
      localStorage.removeItem("arthaai_token");
      localStorage.removeItem("arthaai_user");
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${getApiBase()}/auth/login-json`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: "Login failed" }));
        throw new Error(errorData.detail || "Invalid email or password");
      }

      const data = await res.json();
      const accessToken = data.access_token;
      const loggedUser: User = data.user;

      setToken(accessToken);
      setUser(loggedUser);
      localStorage.setItem("arthaai_token", accessToken);
      localStorage.setItem("arthaai_user", JSON.stringify(loggedUser));

      if (loggedUser.onboarding_completed) {
        router.replace("/dashboard");
      } else {
        router.replace("/onboarding");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (fullName: string, email: string, password: string) => {
    setIsLoading(true);
    try {
      // 1. Register User in PostgreSQL
      const res = await fetch(`${getApiBase()}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Registration failed" }));
        throw new Error(err.detail || "Failed to register account");
      }

      // 2. Auto-login immediately upon registration to obtain JWT
      const loginRes = await fetch(`${getApiBase()}/auth/login-json`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!loginRes.ok) {
        throw new Error("Account created, please log in.");
      }

      const loginData = await loginRes.json();
      const accessToken = loginData.access_token;
      const loggedUser: User = loginData.user;
      loggedUser.onboarding_completed = false;

      setToken(accessToken);
      setUser(loggedUser);
      localStorage.setItem("arthaai_token", accessToken);
      localStorage.setItem("arthaai_user", JSON.stringify(loggedUser));

      // 3. Navigate straight into interactive Onboarding (NEVER straight to dashboard)
      router.replace("/onboarding");
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("arthaai_token");
    localStorage.removeItem("arthaai_user");
    router.replace("/login");
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, signup, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
