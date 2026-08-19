/**
 * Shared helpers for calling the PlanFlow FastAPI backend.
 */

import { getApiBaseUrl } from "./api";

export async function apiFetch<T>(
  path: string,
  token: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") {
        detail = body.detail;
      } else if (body.detail != null) {
        detail = JSON.stringify(body.detail);
      }
    } catch {
      // keep statusText
    }
    throw new Error(`API ${res.status}: ${detail}`);
  }

  return (await res.json()) as T;
}
