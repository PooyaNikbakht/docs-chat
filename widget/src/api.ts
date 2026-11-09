import { readStream } from "./sse";
import type { BookingAction, BotConfig, StreamEvent } from "./types";

export class WidgetError extends Error {
  constructor(
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

const OFFLINE = "We can't reach the assistant right now. Check your connection and try again.";

async function request(url: string, init?: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(url, init);
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new WidgetError("offline", OFFLINE);
  }
  if (!res.ok) throw await toError(res);
  return res;
}

async function toError(res: Response): Promise<WidgetError> {
  try {
    const body = await res.json();
    const error = body?.error;
    if (error?.message) return new WidgetError(error.code ?? "http_error", error.message);
  } catch {
    // Not JSON.
  }
  return new WidgetError("http_error", `Something went wrong (error ${res.status}). Please try again.`);
}

export async function fetchBotConfig(api: string, bot: string): Promise<BotConfig> {
  const res = await request(`${api}/bots/${encodeURIComponent(bot)}`);
  return res.json();
}

export interface DocumentInfo {
  id: string;
  name: string;
  pages: number;
  suggestions: string[];
}

export async function fetchDocument(api: string, id: string): Promise<DocumentInfo> {
  const res = await request(`${api}/documents/${encodeURIComponent(id)}`);
  return res.json();
}

/** POST a question and call `onEvent` for each streamed event. */
export async function ask(
  url: string,
  question: string,
  sessionId: string,
  onEvent: (event: StreamEvent) => void,
  signal: AbortSignal,
  action?: BookingAction,
): Promise<void> {
  const res = await request(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(action ? { question, session_id: sessionId, action } : { question, session_id: sessionId }),
    signal,
  });
  if (!res.body) throw new WidgetError("offline", OFFLINE);
  await readStream(res.body, onEvent);
}
