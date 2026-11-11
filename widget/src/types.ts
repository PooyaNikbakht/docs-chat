export type ProviderName = "anthropic" | "openai" | "mock";

export interface Citation {
  index: number;
  chunk_id: string;
  page: number;
  quote: string;
  context: string;
}

/** A page on the business's site, offered under answers that draw on a help center page. */
export interface PageLink {
  page: number;
  label: string;
  url: string;
}

export interface ChoiceOption {
  id: string;
  label: string;
  detail?: string | null;
}

export interface Choices {
  kind: "service" | "day" | "slot";
  label: string;
  options: ChoiceOption[];
}

export interface BookingSummary {
  /** `awaiting_payment`: the time is held while the visitor pays the deposit at `paymentUrl`. */
  status: "pending" | "confirmed" | "awaiting_payment";
  service: string;
  when: string;
  staff?: string | null;
  name: string;
  contact: string;
  price?: string | null;
  reference?: string | null;
  paymentUrl?: string | null;
  deposit?: string | null;
}

/** A tap sent with the question: a choice chip, or a button on the booking card. */
export interface BookingAction {
  type: "service" | "day" | "slot" | "confirm" | "change";
  id?: string;
}

export type StreamEvent =
  | { type: "meta"; provider: ProviderName; notice: string | null }
  | { type: "text"; text: string }
  | ({ type: "citation" } & Citation)
  | ({ type: "choices" } & Choices)
  | ({ type: "booking"; payment_url?: string | null } & Omit<BookingSummary, "paymentUrl">)
  | { type: "done"; provider: ProviderName; grounded: boolean; citations: number; handoff?: boolean }
  | { type: "error"; code: string; message: string };

/** Public bot config from GET /bots/{id}, merged with the script tag's data attributes. */
export interface BotConfig {
  name: string;
  subline: string;
  greeting: string;
  suggestions: string[];
  accent_color: string;
  handoff_text: string;
  handoff_url: string;
  tooltip: string | null;
  source_label: string;
  /** Source chips under answers. On for "ask this document"; business bots turn it off. */
  show_sources: boolean;
  /** Offered instead of source chips when show_sources is off. */
  page_links: PageLink[];
  mode: "live" | "demo" | "unknown";
}

export interface WidgetOptions {
  /** Base URL of the API, without a trailing slash. */
  api: string;
  /** Answer as a configured bot... */
  bot?: string;
  /** ...or from a temporary uploaded document (the "try your own PDF" page). */
  document?: string;
  position: "right" | "left";
  /** Open the panel on load (once per session). */
  open: boolean;
  overrides: Partial<BotConfig>;
}

export type MessageStatus = "streaming" | "done" | "error" | "stopped";

export interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  citations: Citation[];
  status: MessageStatus;
  handoff?: boolean;
  error?: string;
  notice?: string | null;
  /** For assistant errors: the question to retry. */
  retry?: string;
  /** Booking bots: tappable choices, and a booking to confirm or that was made. */
  choices?: Choices;
  booking?: BookingSummary;
  /** Set once the visitor answered this message's choices or card, so they go quiet. */
  answered?: boolean;
}
