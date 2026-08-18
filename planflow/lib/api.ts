/**
 * Backend API base URL for PlanFlow.
 *
 * Beginner note:
 * - Next.js (this app) usually runs at http://localhost:3000
 * - FastAPI usually runs at http://localhost:8000
 * - Set NEXT_PUBLIC_PLANFLOW_API_URL in `.env.local` if you change the port.
 */
export function getApiBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_PLANFLOW_API_URL?.trim();
  if (fromEnv) {
    return fromEnv.replace(/\/$/, "");
  }
  return "http://127.0.0.1:8000";
}
