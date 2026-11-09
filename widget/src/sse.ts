import type { StreamEvent } from "./types";

const BOUNDARY = /\r?\n\r?\n|\r\r/;

/** Parse one server-sent event block. Returns null for comments, keep-alives and bad JSON. */
export function parseBlock(block: string): StreamEvent | null {
  const data = block
    .split(/\r?\n|\r/)
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).replace(/^ /, ""))
    .join("\n");
  if (!data) return null;
  try {
    const event = JSON.parse(data) as StreamEvent;
    return event && typeof event === "object" && typeof event.type === "string" ? event : null;
  } catch {
    return null;
  }
}

/**
 * Incremental SSE parser. Feed it decoded text as it arrives; it calls `onEvent` for each
 * complete event, however the network split the bytes.
 */
export function createSSEParser(onEvent: (event: StreamEvent) => void) {
  let buffer = "";
  return {
    push(text: string) {
      buffer += text;
      for (;;) {
        const match = BOUNDARY.exec(buffer);
        if (!match) break;
        const block = buffer.slice(0, match.index);
        buffer = buffer.slice(match.index + match[0].length);
        const event = parseBlock(block);
        if (event) onEvent(event);
      }
    },
    /** Call when the stream ends, for a final event without a trailing blank line. */
    flush() {
      const rest = buffer;
      buffer = "";
      if (rest.trim()) {
        const event = parseBlock(rest);
        if (event) onEvent(event);
      }
    },
  };
}

/** Read a fetch Response body as SSE until it ends. */
export async function readStream(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const parser = createSSEParser(onEvent);
  const reader = body.getReader();
  const decoder = new TextDecoder();
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    parser.push(decoder.decode(value, { stream: true }));
  }
  parser.push(decoder.decode());
  parser.flush();
}
