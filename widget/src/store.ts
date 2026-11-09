import type { Message } from "./types";

export interface SavedState {
  v: 1;
  sessionId: string;
  messages: Message[];
  open: boolean;
}

const MAX_MESSAGES = 40;

/** Storage can be missing or throw (private mode, blocked cookies), so every call is guarded. */
function storage(kind: "sessionStorage" | "localStorage"): Storage | null {
  try {
    return window[kind];
  } catch {
    return null;
  }
}

export function newSessionId(): string {
  try {
    return crypto.randomUUID();
  } catch {
    return `s${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
  }
}

export function loadState(key: string): SavedState | null {
  try {
    const raw = storage("sessionStorage")?.getItem(key);
    if (!raw) return null;
    const state = JSON.parse(raw) as SavedState;
    if (state?.v !== 1 || typeof state.sessionId !== "string" || !Array.isArray(state.messages)) {
      return null;
    }
    // An answer cut off by a page change is kept, marked as stopped.
    for (const m of state.messages) if (m.status === "streaming") m.status = "stopped";
    return state;
  } catch {
    return null;
  }
}

export function saveState(key: string, state: SavedState): void {
  try {
    const trimmed = { ...state, messages: state.messages.slice(-MAX_MESSAGES) };
    storage("sessionStorage")?.setItem(key, JSON.stringify(trimmed));
  } catch {
    // Storage full or unavailable: the chat still works, it just won't survive a reload.
  }
}

export function clearState(key: string): void {
  try {
    storage("sessionStorage")?.removeItem(key);
  } catch {
    // ignore
  }
}

export function getFlag(key: string): boolean {
  try {
    return storage("localStorage")?.getItem(key) === "1";
  } catch {
    return false;
  }
}

export function setFlag(key: string): void {
  try {
    storage("localStorage")?.setItem(key, "1");
  } catch {
    // ignore
  }
}
