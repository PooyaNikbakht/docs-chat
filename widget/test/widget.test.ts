import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Widget } from "../src/widget";
import type { StreamEvent, WidgetOptions } from "../src/types";

const CONFIG = {
  id: "northwind",
  name: "Northwind Help",
  business: "Northwind Coffee Co.",
  subline: "Answers from Northwind's help center",
  greeting: "Hi! Ask me about orders.",
  suggestions: ["Can I pause my subscription?", "How long does shipping take?"],
  accent_color: "#3B2A20",
  handoff_text: "Talk to a human",
  handoff_url: "https://northwind.example/contact",
  tooltip: "Questions? Ask me.",
  source_label: "Help center",
  mode: "demo",
};

const ANSWER: StreamEvent[] = [
  { type: "meta", provider: "mock", notice: null },
  { type: "text", text: "You can pause your subscription " },
  { type: "text", text: "for up to 3 months." },
  { type: "citation", index: 1, chunk_id: "p4", page: 4, quote: "You can pause", context: "You can pause it." },
  { type: "done", provider: "mock", grounded: true, citations: 1, handoff: false },
];

const NOT_FOUND: StreamEvent[] = [
  { type: "meta", provider: "mock", notice: null },
  { type: "text", text: "I couldn't find that in our help center." },
  { type: "done", provider: "mock", grounded: false, citations: 0, handoff: true },
];

function sse(events: StreamEvent[]): Response {
  const body = events.map((e) => `event: ${e.type}\ndata: ${JSON.stringify(e)}\n\n`).join("");
  return new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } });
}

const OPTIONS: WidgetOptions = { api: "https://api.example", bot: "northwind", position: "right", open: false, overrides: {} };

let fetchMock: ReturnType<typeof vi.fn>;
let widget: Widget | null = null;

function setup(answers: StreamEvent[][] = [ANSWER]) {
  const queue = [...answers];
  fetchMock = vi.fn(async (url: string) => {
    if (url.endsWith("/bots/northwind")) return new Response(JSON.stringify(CONFIG), { status: 200 });
    if (url.endsWith("/ask")) return sse(queue.shift() ?? ANSWER);
    return new Response("{}", { status: 404 });
  });
  vi.stubGlobal("fetch", fetchMock);
}

async function mount(options: Partial<WidgetOptions> = {}) {
  widget = new Widget({ ...OPTIONS, ...options }).mount();
  await vi.waitFor(() => expect(shadow().querySelector(".title")?.textContent).toBe("Northwind Help"));
  return widget;
}

const shadow = () => widget!.host.shadowRoot!;
const $ = <T extends Element = HTMLElement>(sel: string) => shadow().querySelector<T>(sel)!;
const $$ = (sel: string) => [...shadow().querySelectorAll<HTMLElement>(sel)];
const launcher = () => $<HTMLButtonElement>(".launcher");
const panel = () => $(".panel");

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  setup();
});

afterEach(() => {
  widget?.destroy();
  widget = null;
  vi.unstubAllGlobals();
});

describe("widget", () => {
  it("renders in a shadow root with the bot's accent colour and config", async () => {
    await mount();
    expect(widget!.host.tagName.toLowerCase()).toBe("docs-chat-widget");
    expect(document.body.querySelector(".launcher")).toBeNull(); // nothing leaks into the page
    expect($(".dc").style.getPropertyValue("--accent")).toBe("#3B2A20");
    expect($(".subline").textContent).toBe("Answers from Northwind's help center");
    expect(launcher().getAttribute("aria-label")).toBe("Open chat with Northwind Help");
    expect(panel().hidden).toBe(true);
    expect(fetchMock.mock.calls[0][0]).toBe("https://api.example/bots/northwind");
  });

  it("opens with focus inside, closes on Escape and returns focus to the launcher", async () => {
    await mount();
    launcher().click();
    expect(panel().hidden).toBe(false);
    expect(launcher().getAttribute("aria-expanded")).toBe("true");
    await vi.waitFor(() => expect(shadow().activeElement).toBe($(".input")));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    expect(panel().hidden).toBe(true);
    expect(launcher().getAttribute("aria-expanded")).toBe("false");
    expect(shadow().activeElement).toBe(launcher());
  });

  it("shows the greeting and suggestions, and a suggestion asks the question", async () => {
    await mount();
    launcher().click();
    expect($(".greeting .bubble").textContent).toBe("Hi! Ask me about orders.");
    const chips = $$(".chip");
    expect(chips.map((c) => c.textContent)).toEqual(CONFIG.suggestions);

    chips[0].click();
    await vi.waitFor(() => expect($$(".msg.assistant:not(.greeting) .chip-source")).toHaveLength(1));
    const [, request] = fetchMock.mock.calls.find(([u]) => String(u).endsWith("/ask"))!;
    expect(JSON.parse(request.body)).toMatchObject({ question: "Can I pause my subscription?" });
    expect($$(".msg.user .bubble").map((b) => b.textContent)).toEqual(["Can I pause my subscription?"]);
    expect($(".msg.assistant:not(.greeting) .bubble").textContent).toBe(
      "You can pause your subscription for up to 3 months.",
    );
    expect($(".chip-source").textContent).toBe("Help center, p. 4");
    expect($$(".chip")).toHaveLength(0); // suggestions hide once the chat starts
    expect($$(".handoff")).toHaveLength(0);
    expect($(".tag").hidden).toBe(false); // demo mode
  });

  it("offers the human handoff on a not-covered answer", async () => {
    setup([NOT_FOUND]);
    await mount();
    launcher().click();
    await widget!.send("Do you sell laptops?");
    const handoff = $<HTMLAnchorElement>(".msg.assistant:not(.greeting) .handoff");
    expect(handoff.textContent).toBe("Talk to a human");
    expect(handoff.href).toBe("https://northwind.example/contact");
    // The footer link is always there too.
    expect($<HTMLAnchorElement>(".foot a").href).toBe("https://northwind.example/contact");
  });

  it("keeps the conversation in sessionStorage across page loads", async () => {
    await mount();
    launcher().click();
    await widget!.send("Can I pause my subscription?");
    const firstSession = JSON.parse(String(fetchMock.mock.calls.at(-1)![1].body)).session_id;
    widget!.destroy();

    await mount(); // a new page with the same snippet
    expect(panel().hidden).toBe(false); // it was open, so it stays open
    expect($$(".msg.user").length).toBe(1);
    expect($(".chip-source").textContent).toBe("Help center, p. 4");

    await widget!.send("How do I cancel it?");
    const secondSession = JSON.parse(String(fetchMock.mock.calls.at(-1)![1].body)).session_id;
    expect(secondSession).toBe(firstSession); // follow-ups keep the server-side history
  });

  it("shows a friendly error with a retry when the request fails", async () => {
    await mount();
    fetchMock.mockImplementationOnce(async () =>
      new Response(JSON.stringify({ error: { code: "rate_limited", message: "Too many questions." } }), { status: 429 }),
    );
    launcher().click();
    await widget!.send("Hello?");
    expect($(".msg.error .bubble").textContent).toContain("Too many questions.");
    $<HTMLButtonElement>(".retry").click();
    await vi.waitFor(() => expect($$(".msg.error")).toHaveLength(0));
    expect($$(".msg.user")).toHaveLength(1);
  });

  it("announces the answer and its sources for screen readers", async () => {
    await mount();
    launcher().click();
    await widget!.send("Can I pause my subscription?");
    const live = $(".sr-only[aria-live='polite']");
    expect(live.textContent).toContain("You can pause your subscription for up to 3 months.");
    expect(live.textContent).toContain("Sources: Help center, p. 4.");
  });

  it("starts a new conversation with a fresh session", async () => {
    await mount();
    launcher().click();
    await widget!.send("Can I pause my subscription?");
    $<HTMLButtonElement>("[aria-label='Start a new conversation']").click();
    expect($$(".msg.user")).toHaveLength(0);
    expect($$(".chip")).toHaveLength(2);
  });

  it("shows open times as chips, sends the tap as an action, and confirms on a card", async () => {
    const offer: StreamEvent[] = [
      { type: "meta", provider: "mock", notice: null },
      { type: "text", text: "Yes, we have 2:00 PM and 3:30 PM open on Saturday. Want me to book one?" },
      {
        type: "choices",
        kind: "slot",
        label: "Open times, Sat, Nov 14",
        options: [
          { id: "fade-202611141400", label: "2:00 PM" },
          { id: "fade-202611141530", label: "3:30 PM" },
        ],
      },
      { type: "done", provider: "mock", grounded: false, citations: 0, handoff: false },
    ];
    const card: StreamEvent[] = [
      { type: "meta", provider: "mock", notice: null },
      { type: "text", text: "Here's what I'll book. Shall I go ahead?" },
      {
        type: "booking",
        status: "pending",
        service: "Skin fade",
        when: "Sat, Nov 14, 2:00 PM",
        staff: "Marcus",
        name: "Alex Chen",
        contact: "alex@example.com",
        price: "$45",
        reference: null,
      },
      { type: "done", provider: "mock", grounded: false, citations: 0, handoff: false },
    ];
    const booked: StreamEvent[] = [
      { type: "meta", provider: "mock", notice: null },
      { type: "text", text: "You're booked, Alex." },
      { ...(card[2] as object), status: "confirmed", reference: "KC-1A2B3C" } as StreamEvent,
      { type: "done", provider: "mock", grounded: false, citations: 0, handoff: false },
    ];
    setup([offer, card, card, booked]);
    await mount();
    launcher().click();
    await widget!.send("Is Saturday open for a fade?");

    const group = $(".choices");
    expect(group.getAttribute("role")).toBe("group");
    expect(shadow().getElementById(group.getAttribute("aria-labelledby")!)!.textContent).toBe("Open times, Sat, Nov 14");
    const times = $$(".choice");
    expect(times.map((b) => b.textContent)).toEqual(["2:00 PM", "3:30 PM"]);
    expect($(".sr-only[aria-live='polite']").textContent).toContain("Open times, Sat, Nov 14: 2:00 PM, 3:30 PM.");

    times[0].click();
    await vi.waitFor(() => expect($$(".booking")).toHaveLength(1));
    const asks = () => fetchMock.mock.calls.filter(([u]) => String(u).endsWith("/ask"));
    expect(JSON.parse(asks()[1][1].body)).toMatchObject({
      question: "2:00 PM, Sat, Nov 14",
      action: { type: "slot", id: "fade-202611141400" },
    });
    expect($$(".choice")).toHaveLength(0); // answered choices go quiet
    expect($(".booking-head").textContent).toBe("Check the details");
    expect($$(".booking-row").map((r) => r.textContent)).toContain("WhenSat, Nov 14, 2:00 PM");

    // A typed message instead of a tap retires the old card's buttons.
    await widget!.send("Alex Chen, alex@example.com");
    expect($$(".booking .confirm")).toHaveLength(1);

    $<HTMLButtonElement>(".booking .confirm").click();
    await vi.waitFor(() => expect($$(".booking.confirmed")).toHaveLength(1));
    expect(JSON.parse(asks().at(-1)![1].body).action).toEqual({ type: "confirm" });
    expect($$(".booking .confirm")).toHaveLength(0);
    expect($(".booking.confirmed").textContent).toContain("KC-1A2B3C");
    expect($(".sr-only[aria-live='polite']").textContent).toContain("Booked: Skin fade, Sat, Nov 14, 2:00 PM with Marcus.");
  });

  it("shows a held booking with a pay deposit link, only to Stripe Checkout", async () => {
    const held = (url: string): StreamEvent[] => [
      { type: "meta", provider: "mock", notice: null },
      { type: "text", text: "Almost done, Alex." },
      {
        type: "booking",
        status: "awaiting_payment",
        service: "Skin fade",
        when: "Sat, Nov 14, 2:00 PM",
        staff: "Marcus",
        name: "Alex Chen",
        contact: "alex@example.com",
        price: "$45",
        reference: "bk_1",
        payment_url: url,
        deposit: "$10",
      },
      { type: "done", provider: "mock", grounded: false, citations: 0, handoff: false },
    ];
    setup([held("https://checkout.stripe.com/c/pay/cs_test_1"), held("https://evil.example/pay")]);
    await mount();
    launcher().click();
    await widget!.send("Book it");
    await vi.waitFor(() => expect($$(".booking.awaiting_payment")).toHaveLength(1));
    const pay = $<HTMLAnchorElement>(".booking a.confirm");
    expect(pay.textContent).toBe("Pay $10 deposit");
    expect(pay.href).toBe("https://checkout.stripe.com/c/pay/cs_test_1");
    expect(pay.target).toBe("_blank");
    expect(pay.rel).toContain("noopener");
    expect($(".booking-head").textContent).toBe("Held for 30 minutes");
    expect($(".sr-only[aria-live='polite']").textContent).toContain("Pay the $10 deposit to confirm it.");

    await widget!.send("Book it");
    await vi.waitFor(() => expect($$(".booking")).toHaveLength(2));
    expect($$(".booking a.confirm")).toHaveLength(1); // the second card's link wasn't Stripe's
  });
});
