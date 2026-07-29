/* ── Auth Context ───────────────────────────────────────────────────

   AuthProvider with login/logout, localStorage token persistence.
   Wraps the app to provide user state and auth methods via React Context.
*/

"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import type { UserResponse } from "@/lib/api/types";

interface AuthContextValue {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function ensureToken() {
      try {
        const existingToken = localStorage.getItem("access_token");
        if (!existingToken) {
          const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
          const res = await fetch(`${apiBase}/auth/dev-token`, { method: "POST" });
          if (res.ok) {
            const data = await res.json();
            if (data.access_token) {
              localStorage.setItem("access_token", data.access_token);
              if (data.refresh_token) {
                localStorage.setItem("refresh_token", data.refresh_token);
              }
            }
          }
        }
      } catch (err) {
        console.error("Failed to acquire dev token:", err);
      } finally {
        setIsLoading(false);
      }
    }
    ensureToken();
  }, []);

  const login = async (email: string, password: string) => {
    // No-op — login disabled
    void email;
    void password;
  };

  const logout = () => {
    // No-op — login disabled
  };

  return (
    <AuthContext.Provider
      value={{
        user: {
          id: "dev-user",
          email: "dev@localhost",
          role: "recruiter",
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        isLoading,
        isAuthenticated: true,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
