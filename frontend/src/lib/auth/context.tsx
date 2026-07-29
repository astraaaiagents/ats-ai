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
import { api, getToken, setToken, clearTokens } from "@/lib/api/client";
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
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Restore session from localStorage on mount
    const token = getToken();
    if (token) {
      // Validate token by fetching user profile
      api
        .get<UserResponse>("/users/me")
        .then((u) => setUser(u))
        .catch(() => clearTokens())
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const data = await api.post<{ access_token: string; refresh_token: string }>(
      "/auth/login",
      { email, password }
    );
    setToken(data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    // Fetch user profile
    const user = await api.get<UserResponse>("/users/me");
    setUser(user);
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
