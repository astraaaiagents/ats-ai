/* ── API Client ─────────────────────────────────────────────────────

   Fetch wrapper with JWT Bearer token, auto-refresh on 401.
   All API calls go through this client to centralize auth handling.
*/

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/* ── Token storage ────────────────────────────────────────────────── */

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("access_token", token);
}

function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

/* ── Refresh logic ────────────────────────────────────────────────── */

let refreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

async function refreshAccessToken(): Promise<string> {
  if (refreshing) {
    return new Promise((resolve) => {
      addRefreshSubscriber(resolve);
    });
  }

  refreshing = true;
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) {
    clearTokens();
    throw new Error("No refresh token");
  }

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) {
      clearTokens();
      throw new Error("Token refresh failed");
    }

    const data = await res.json();
    setToken(data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    onTokenRefreshed(data.access_token);
    return data.access_token;
  } catch (err) {
    clearTokens();
    throw err;
  } finally {
    refreshing = false;
  }
}

/* ── Fetch wrapper ────────────────────────────────────────────────── */

interface ApiOptions extends RequestInit {
  skipAuth?: boolean;
}

async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { skipAuth, headers: extraHeaders, ...rest } = options;

  let token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (extraHeaders) {
    if (extraHeaders instanceof Headers) {
      extraHeaders.forEach((val, key) => {
        headers[key] = val;
      });
    } else if (Array.isArray(extraHeaders)) {
      extraHeaders.forEach(([key, val]) => {
        headers[key] = val;
      });
    } else {
      Object.assign(headers, extraHeaders as Record<string, string>);
    }
  }

  if (!skipAuth) {
    headers["Authorization"] = token ? `Bearer ${token}` : "Bearer dev-token";
  }

  let response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers,
  });

  // Auto-refresh on 401
  if (response.status === 401 && !skipAuth) {
    try {
      token = await refreshAccessToken();
      headers["Authorization"] = `Bearer ${token}`;
      response = await fetch(`${API_BASE}${path}`, {
        ...rest,
        headers,
      });
    } catch {
      // Refresh failed — user will be redirected to login
      throw new Error("Authentication required");
    }
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const msg =
      body?.error?.message ||
      (typeof body?.error === "string" ? body.error : null) ||
      (typeof body?.detail === "string" ? body.detail : null) ||
      `API error: ${response.status}`;
    throw new Error(msg);
  }

  // Handle 204 No Content
  if (response.status === 204) return undefined as T;

  return response.json();
}

/* ── Public API ───────────────────────────────────────────────────── */

export const api = {
  get: <T>(path: string, options?: ApiOptions) => apiFetch<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: ApiOptions) =>
    apiFetch<T>(path, { ...options, method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown, options?: ApiOptions) =>
    apiFetch<T>(path, { ...options, method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown, options?: ApiOptions) =>
    apiFetch<T>(path, { ...options, method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string, options?: ApiOptions) => apiFetch<T>(path, { ...options, method: "DELETE" }),
};

/* ── Token helpers (exported for auth context) ────────────────────── */

export { getToken, setToken, clearTokens };
