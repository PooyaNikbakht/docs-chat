import { describe, expect, it } from "vitest";
import { createSSEParser, parseBlock, readStream } from "../src/sse";
import type { StreamEvent } from "../src/types";

const frame = (event: StreamEvent) => `event: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`;

const EVENTS: StreamEvent[] = [
  { type: "meta", provider: "mock", notice: null },
  { type: "text", text: "You can pause " },
  { type: "text", text: "for up to 3 months." },
  { type: "citation", index: 1, chunk_id: "p4-c001", page: 4, quote: "You can pause", context: "You can pause it." },
  { type: "done", provider: "mock", grounded: true, citations: 1, handoff: false },
];

function collect(chunks: string[]): StreamEvent[] {
  const out: StreamEvent[] = [];
  const parser = createSSEParser((e) => out.push(e));
  for (const c of chunks) parser.push(c);
  parser.flush();
  return out;
}

describe("SSE parser", () => {
  it("parses whole events", () => {
    expect(collect([EVENTS.map(frame).join("")])).toEqual(EVENTS);
  });

  it("handles events split at every possible byte", () => {
    const body = EVENTS.map(frame).join("");
    for (let size = 1; size < 40; size += 3) {
      const chunks: string[] = [];
      for (let i = 0; i < body.length; i += size) chunks.push(body.slice(i, i + size));
      expect(collect(chunks)).toEqual(EVENTS);
    }
  });

  it("accepts CRLF line endings, even split between chunks", () => {
    const body = EVENTS.map(frame).join("").replace(/\n/g, "\r\n");
    const chunks = body.split(/(?<=\r)/); // split right after every \r
    expect(collect(chunks)).toEqual(EVENTS);
  });

  it("emits a final event without a trailing blank line on flush", () => {
    const last = frame(EVENTS[4]).trimEnd();
    expect(collect([frame(EVENTS[0]), last])).toEqual([EVENTS[0], EVENTS[4]]);
  });

  it("ignores comments, keep-alives and malformed data", () => {
    const body = `: keep-alive\n\ndata: {not json\n\nevent: x\n\ndata: 42\n\n${frame(EVENTS[1])}`;
    expect(collect([body])).toEqual([EVENTS[1]]);
  });

  it("joins multi-line data fields", () => {
    expect(parseBlock('data: {"type":"text",\ndata: "text":"hi"}')).toEqual({ type: "text", text: "hi" });
  });

  it("reads a byte stream with multi-byte characters split across chunks", async () => {
    const bytes = new TextEncoder().encode(frame({ type: "text", text: "Café, 94 °C" }));
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        for (const b of bytes) controller.enqueue(new Uint8Array([b]));
        controller.close();
      },
    });
    const out: StreamEvent[] = [];
    await readStream(stream, (e) => out.push(e));
    expect(out).toEqual([{ type: "text", text: "Café, 94 °C" }]);
  });
});
