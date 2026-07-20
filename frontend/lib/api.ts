// Typed API client. One place that knows about transport, auth headers, and
// error shape — components just call these functions.

import type {
  CompareResult,
  ScanRecord,
  ScanResult,
  ScanSummary,
  TokenResponse,
  User,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const TOKEN_KEY = "catchy_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  if (typeof window === "undefined") return;
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable (private mode) — session stays in memory only */
  }
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  let resp: Response;
  try {
    resp = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(
      "Cannot reach the API. Is the backend running on :8000?",
      0,
    );
  }

  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`;
    try {
      const body = await resp.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
        detail = body.detail[0].msg;
      }
    } catch {
      /* non-JSON error body — keep the generic message */
    }
    throw new ApiError(detail, resp.status);
  }

  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

/** Analyze returns the scan plus the saved id (when signed in). */
export interface AnalyzeResponse {
  result: ScanResult;
  scanId: string | null;
}

async function analyzeRequest(
  path: string,
  init: RequestInit,
): Promise<AnalyzeResponse> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  let resp: Response;
  try {
    resp = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(
      "Cannot reach the API. Is the backend running on :8000?",
      0,
    );
  }
  if (!resp.ok) {
    let detail = `Scan failed (${resp.status})`;
    try {
      const body = await resp.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* keep generic */
    }
    throw new ApiError(detail, resp.status);
  }
  const result = (await resp.json()) as ScanResult;
  return { result, scanId: resp.headers.get("X-Scan-Id") };
}

export const api = {
  analyzeText: (rawEmail: string) =>
    analyzeRequest("/scan/analyze", {
      method: "POST",
      body: JSON.stringify({ raw_email: rawEmail }),
    }),

  analyzeFile: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return analyzeRequest("/scan/analyze/file", { method: "POST", body: form });
  },

  register: (email: string, password: string) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<User>("/auth/me"),

  listScans: (limit = 50) => request<ScanSummary[]>(`/scans?limit=${limit}`),

  getScan: (id: string) => request<ScanRecord>(`/scans/${id}`),

  compareScans: (a: string, b: string) =>
    request<CompareResult>(`/scans/compare?a=${a}&b=${b}`),
};
