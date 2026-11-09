import { site } from "@/config/site";
import type { DocumentInfo, Health } from "./types";

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status = 0,
  ) {
    super(message);
  }
}

const OFFLINE_MESSAGE =
  "We can't reach the server right now. Check your connection, or try again in a minute.";

async function request(path: string, init?: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`${site.apiUrl}${path}`, init);
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("offline", OFFLINE_MESSAGE);
  }
  if (!res.ok) throw await toApiError(res);
  return res;
}

async function toApiError(res: Response): Promise<ApiError> {
  try {
    const body = await res.json();
    if (body?.error?.message) {
      return new ApiError(body.error.code, friendly(body.error.code, body.error.message), res.status);
    }
  } catch {
    // not JSON, fall through
  }
  return new ApiError("http_error", `The server returned an error (${res.status}).`, res.status);
}

function friendly(code: string, message: string): string {
  if (code === "rate_limited") return `${message} The limit keeps the public demo free.`;
  return message;
}

export async function getHealth(): Promise<Health> {
  const res = await request("/health", { cache: "no-store" });
  return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentInfo> {
  const form = new FormData();
  form.append("file", file);
  const res = await request("/documents", { method: "POST", body: form });
  return res.json();
}

export async function loadSample(): Promise<DocumentInfo> {
  const res = await request("/documents/sample", { method: "POST" });
  return res.json();
}
