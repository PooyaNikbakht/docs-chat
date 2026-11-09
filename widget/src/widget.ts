import { WidgetError, ask, fetchBotConfig, fetchDocument } from "./api";
import { DEFAULTS, mergeConfig, onAccent } from "./config";
import { h, icon } from "./dom";
import { icons } from "./icons";
import { renderText } from "./markdown";
import {
  groupSources,
  relatedLinks,
  renderLinks,
  renderSources,
  sourceLabel,
} from "./sources";
import {
  clearState,
  getFlag,
  loadState,
  newSessionId,
  saveState,
  setFlag,
} from "./store";
import { css } from "./styles";
import type {
  BookingAction,
  BookingSummary,
  BotConfig,
  Choices,
  Message,
  StreamEvent,
  WidgetOptions,
} from "./types";

const TOOLTIP_DELAY_MS = 1500;
const NARROW = "(max-width: 480px)";

let instanceCount = 0;

/** The chat widget: a launcher bubble and a panel, rendered inside a Shadow DOM. */
export class Widget {
  readonly host: HTMLElement;
  private readonly root: ShadowRoot;
  private readonly uid = `dc${++instanceCount}`;
  private readonly storageKey: string;
  private readonly tooltipKey: string;

  private config: BotConfig = DEFAULTS;
  private configError: string | null = null;
  private ready = false;
  // Hides the widget until its config arrives, so it never shows the default name and colour first.
  private pendingStyle!: HTMLStyleElement;
  private messages: Message[] = [];
  private sessionId: string;
  private isOpen = false;
  private controller: AbortController | null = null;
  private demo = false;
  private announced = 0;

  // Elements
  private shell!: HTMLDivElement;
  private launcher!: HTMLButtonElement;
  private tooltip: HTMLDivElement | null = null;
  private panel!: HTMLDivElement;
  private titleEl!: HTMLHeadingElement;
  private sublineEl!: HTMLParagraphElement;
  private avatar!: HTMLSpanElement;
  private log!: HTMLDivElement;
  private live!: HTMLDivElement;
  private input!: HTMLTextAreaElement;
  private sendButton!: HTMLButtonElement;
  private handoffLink!: HTMLAnchorElement;
  private demoTag!: HTMLSpanElement;

  constructor(private readonly options: WidgetOptions) {
    const target = options.bot
      ? `bot:${options.bot}`
      : `doc:${options.document}`;
    this.storageKey = `docs-chat:${target}`;
    this.tooltipKey = `docs-chat:tooltip:${target}`;
    const saved = loadState(this.storageKey);
    this.sessionId = saved?.sessionId ?? newSessionId();
    this.messages = saved?.messages ?? [];
    this.isOpen = saved?.open ?? false;

    this.host = document.createElement("docs-chat-widget");
    this.host.setAttribute("data-target", target);
    this.root = this.host.attachShadow({ mode: "open" });
    this.build();
  }

  // ---- lifecycle ----

  mount(parent: HTMLElement = document.body): this {
    parent.appendChild(this.host);
    this.renderAll();
    void this.loadConfig();
    if (this.isOpen || (this.options.open && !loadState(this.storageKey))) {
      this.open(false);
    } else {
      this.scheduleTooltip();
    }
    return this;
  }

  destroy(): void {
    this.controller?.abort();
    document.removeEventListener("keydown", this.onKeydown, true);
    this.host.remove();
  }

  private async loadConfig(): Promise<void> {
    const { api, bot, document: docId, overrides } = this.options;
    try {
      let server: Partial<BotConfig> = {};
      if (bot) {
        server = await fetchBotConfig(api, bot);
      } else if (docId) {
        const doc = await fetchDocument(api, docId);
        const short =
          doc.name
            .replace(/\.pdf$/i, "")
            .replace(/[-_]+/g, " ")
            .trim() || "this document";
        server = {
          subline: `Answers from ${doc.name}`,
          greeting: `Hi! Ask me anything about "${short}". I'll answer from the document and show the page I used.`,
          suggestions: doc.suggestions,
          source_label: short.length > 24 ? `${short.slice(0, 22)}...` : short,
        };
      }
      this.config = mergeConfig(server, overrides);
      this.configError = null;
    } catch (err) {
      this.config = mergeConfig({}, overrides);
      this.configError =
        err instanceof WidgetError && err.code === "not_found"
          ? "This assistant isn't available anymore."
          : "The assistant can't be reached right now. Please try again later.";
    }
    this.demo = this.demo || this.config.mode === "demo";
    this.ready = true;
    this.applyConfig();
    this.renderAll();
    this.pendingStyle.remove();
  }

  // ---- building the DOM ----

  private build(): void {
    const style = document.createElement("style");
    style.textContent = css;
    const panelId = `${this.uid}-panel`;
    const titleId = `${this.uid}-title`;

    this.launcher = h(
      "button",
      {
        type: "button",
        class: "launcher",
        "aria-label": "Open chat",
        "aria-expanded": "false",
        "aria-controls": panelId,
        onclick: () => (this.isOpen ? this.close() : this.open()),
      },
      h("span", { class: "icon-chat" }, icon(icons.chat)),
      h("span", { class: "icon-close" }, icon(icons.close)),
    );

    this.avatar = h("span", { class: "avatar", "aria-hidden": "true" });
    this.titleEl = h("h2", { class: "title", id: titleId });
    this.sublineEl = h("p", { class: "subline" });
    const header = h(
      "div",
      { class: "header" },
      this.avatar,
      h("div", { class: "titles" }, this.titleEl, this.sublineEl),
      h(
        "button",
        {
          type: "button",
          class: "head-btn",
          "aria-label": "Start a new conversation",
          title: "New conversation",
          onclick: () => this.reset(),
        },
        icon(icons.restart),
      ),
      h(
        "button",
        {
          type: "button",
          class: "head-btn",
          "aria-label": "Close chat",
          onclick: () => this.close(),
        },
        icon(icons.close),
      ),
    );

    this.log = h("div", {
      class: "log",
      role: "log",
      "aria-label": "Conversation",
      tabindex: "0",
    });
    this.live = h("div", {
      class: "sr-only",
      "aria-live": "polite",
      "aria-atomic": "false",
    });

    this.input = h("textarea", {
      class: "input",
      rows: 1,
      placeholder: "Ask a question",
      "aria-label": "Your question",
      maxlength: 1000,
      enterkeyhint: "send",
    });
    this.input.addEventListener("input", () => this.autosize());
    this.input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        this.submit();
      }
    });
    this.sendButton = h(
      "button",
      { type: "submit", class: "send", "aria-label": "Send" },
      icon(icons.send),
    );
    const form = h(
      "form",
      {
        class: "row",
        onsubmit: (e: Event) => {
          e.preventDefault();
          this.submit();
        },
      },
      this.input,
      this.sendButton,
    );
    this.handoffLink = h(
      "a",
      { target: "_top" },
      icon(icons.person),
      h("span"),
    );
    this.demoTag = h(
      "span",
      {
        class: "tag",
        title: "Answers come from a built-in demo mode, not a live AI model",
        hidden: true,
      },
      "Demo mode",
    );
    const composer = h(
      "div",
      { class: "composer" },
      form,
      h("div", { class: "foot" }, this.handoffLink, this.demoTag),
    );

    this.panel = h(
      "div",
      {
        class: "panel",
        id: panelId,
        role: "dialog",
        "aria-labelledby": titleId,
        tabindex: "-1",
        hidden: true,
      },
      header,
      this.log,
      composer,
      this.live,
    );

    this.shell = h(
      "div",
      { class: `dc ${this.options.position}` },
      this.panel,
      this.launcher,
    );
    this.pendingStyle = document.createElement("style");
    this.pendingStyle.textContent = ":host { visibility: hidden !important; }";
    this.root.append(style, this.pendingStyle, this.shell);
    this.applyConfig();
  }

  private applyConfig(): void {
    const c = this.config;
    this.shell.style.setProperty("--accent", c.accent_color);
    this.shell.style.setProperty("--on-accent", onAccent(c.accent_color));
    this.titleEl.textContent = c.name;
    this.sublineEl.textContent = c.subline;
    this.avatar.textContent = c.name.trim().charAt(0).toUpperCase() || "?";
    this.launcher.setAttribute(
      "aria-label",
      this.isOpen ? `Close chat` : `Open chat with ${c.name}`,
    );
    const hasHandoff = Boolean(c.handoff_url);
    this.handoffLink.hidden = !hasHandoff;
    if (hasHandoff) this.handoffLink.href = c.handoff_url;
    this.handoffLink.lastElementChild!.textContent = c.handoff_text;
    this.demoTag.hidden = !this.demo;
  }

  // ---- open and close ----

  open(focus = true): void {
    this.isOpen = true;
    this.hideTooltip(true);
    this.panel.hidden = false;
    this.shell.classList.add("open");
    this.launcher.setAttribute("aria-expanded", "true");
    this.launcher.setAttribute("aria-label", "Close chat");
    document.addEventListener("keydown", this.onKeydown, true);
    this.persist();
    this.scrollToEnd(true);
    if (focus) {
      // On phones, focusing the input would pop the keyboard over the greeting.
      const target = window.matchMedia?.(NARROW).matches
        ? this.panel
        : this.input;
      requestAnimationFrame(() => target.focus({ preventScroll: true }));
    }
  }

  close(): void {
    if (!this.isOpen) return;
    this.isOpen = false;
    this.panel.hidden = true;
    this.shell.classList.remove("open");
    this.launcher.setAttribute("aria-expanded", "false");
    this.launcher.setAttribute(
      "aria-label",
      `Open chat with ${this.config.name}`,
    );
    document.removeEventListener("keydown", this.onKeydown, true);
    this.persist();
    this.launcher.focus();
  }

  private onKeydown = (e: KeyboardEvent): void => {
    if (e.key === "Escape" && this.isOpen) {
      e.stopPropagation();
      this.close();
    }
  };

  // ---- tooltip ----

  private scheduleTooltip(): void {
    if (getFlag(this.tooltipKey) || this.messages.length) return;
    window.setTimeout(() => {
      if (
        this.isOpen ||
        this.tooltip ||
        !this.ready ||
        !this.config.tooltip ||
        getFlag(this.tooltipKey)
      ) {
        return;
      }
      this.tooltip = h(
        "div",
        { class: "tooltip", role: "status" },
        h(
          "button",
          { type: "button", class: "tooltip-open", onclick: () => this.open() },
          this.config.tooltip,
        ),
        h(
          "button",
          {
            type: "button",
            class: "tooltip-close",
            "aria-label": "Dismiss",
            onclick: () => this.hideTooltip(true),
          },
          icon(icons.closeSmall),
        ),
      );
      this.shell.insertBefore(this.tooltip, this.launcher);
    }, TOOLTIP_DELAY_MS);
  }

  private hideTooltip(remember: boolean): void {
    if (remember) setFlag(this.tooltipKey);
    this.tooltip?.remove();
    this.tooltip = null;
  }

  // ---- conversation ----

  private submit(): void {
    if (this.controller) {
      this.controller.abort();
      return;
    }
    const question = this.input.value.trim();
    if (!question) return;
    this.input.value = "";
    this.autosize();
    void this.send(question);
  }

  async send(question: string, action?: BookingAction): Promise<void> {
    if (this.controller || !this.ready) return;
    // Earlier choices and booking buttons go quiet once the visitor moves on.
    for (const m of this.messages) {
      if (m.choices || m.booking) m.answered = true;
    }
    if (this.configError) {
      this.messages.push(this.userMessage(question), {
        ...this.assistantMessage(),
        status: "error",
        error: this.configError,
      });
      this.renderAll();
      return;
    }
    const answer = this.assistantMessage();
    this.messages.push(this.userMessage(question), answer);
    this.announced = 0;
    this.renderAll();
    this.persist();
    this.scrollToEnd(true);

    const controller = new AbortController();
    this.controller = controller;
    this.setBusy(true);
    const { api, bot, document: docId } = this.options;
    const url = bot
      ? `${api}/bots/${encodeURIComponent(bot)}/ask`
      : `${api}/documents/${encodeURIComponent(docId ?? "")}/ask`;
    try {
      await ask(
        url,
        question,
        this.sessionId,
        (event) => this.onEvent(answer, event),
        controller.signal,
        action,
      );
      if (answer.status === "streaming") answer.status = "done";
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        answer.status = "stopped";
      } else {
        answer.status = "error";
        answer.retry = question;
        answer.error =
          err instanceof WidgetError && err.code === "not_found" && docId
            ? "This document has expired. Upload it again to keep chatting."
            : err instanceof Error
              ? err.message
              : "Something went wrong. Please try again.";
      }
    } finally {
      this.controller = null;
      this.setBusy(false);
      this.updateMessage(answer);
      // New choices or a booking card sit below the text: bring them into view.
      if (answer.choices || answer.booking) this.scrollToEnd(true);
      this.announceRest(answer);
      this.persist();
    }
  }

  private onEvent(answer: Message, event: StreamEvent): void {
    switch (event.type) {
      case "meta":
        answer.notice = event.notice;
        if (event.provider === "mock" && !this.demo) {
          this.demo = true;
          this.applyConfig();
        }
        break;
      case "text":
        answer.text += event.text;
        this.announceProgress(answer);
        break;
      case "citation":
        answer.citations.push({
          index: event.index,
          chunk_id: event.chunk_id,
          page: event.page,
          quote: event.quote,
          context: event.context,
        });
        break;
      case "choices":
        answer.choices = {
          kind: event.kind,
          label: event.label,
          options: event.options,
        };
        break;
      case "booking":
        answer.booking = {
          status: event.status,
          service: event.service,
          when: event.when,
          staff: event.staff,
          name: event.name,
          contact: event.contact,
          price: event.price,
          reference: event.reference,
        };
        break;
      case "done":
        answer.status = "done";
        answer.handoff = event.handoff ?? !event.grounded;
        break;
      case "error":
        answer.status = "error";
        answer.error = event.message;
        break;
    }
    this.updateMessage(answer);
    this.scrollToEnd(false);
  }

  private reset(): void {
    this.controller?.abort();
    this.messages = [];
    this.sessionId = newSessionId();
    clearState(this.storageKey);
    this.renderAll();
    this.persist();
    this.input.focus();
  }

  private userMessage(text: string): Message {
    return {
      id: `${Date.now().toString(36)}u${this.messages.length}`,
      role: "user",
      text,
      citations: [],
      status: "done",
    };
  }

  private assistantMessage(): Message {
    return {
      id: `${Date.now().toString(36)}a${this.messages.length}`,
      role: "assistant",
      text: "",
      citations: [],
      status: "streaming",
    };
  }

  private persist(): void {
    saveState(this.storageKey, {
      v: 1,
      sessionId: this.sessionId,
      messages: this.messages,
      open: this.isOpen,
    });
  }

  // ---- screen reader announcements ----

  /** Announce finished sentences while the answer streams, instead of every token. */
  private announceProgress(answer: Message): void {
    const text = answer.text;
    const end = Math.max(
      text.lastIndexOf(". "),
      text.lastIndexOf("? "),
      text.lastIndexOf("! "),
    );
    if (end + 1 > this.announced) {
      this.say(text.slice(this.announced, end + 1));
      this.announced = end + 1;
    }
  }

  private announceRest(answer: Message): void {
    const rest = answer.text.slice(this.announced).trim();
    const parts: string[] = [];
    if (rest) parts.push(rest);
    const sources = this.config.show_sources
      ? groupSources(answer.citations)
      : [];
    if (sources.length) {
      parts.push(
        `Sources: ${sources.map((s) => sourceLabel(this.config.source_label, s.page)).join(", ")}.`,
      );
    }
    const links = this.config.show_sources
      ? []
      : relatedLinks(answer.citations, this.config.page_links);
    if (links.length)
      parts.push(`Related pages: ${links.map((l) => l.label).join(", ")}.`);
    if (answer.choices?.options.length) {
      parts.push(
        `${answer.choices.label}: ${answer.choices.options.map((o) => o.label).join(", ")}.`,
      );
    }
    if (answer.booking) parts.push(bookingSentence(answer.booking));
    if (answer.status === "error" && answer.error) parts.push(answer.error);
    if (parts.length) this.say(parts.join(" "));
    this.announced = answer.text.length;
  }

  private say(text: string): void {
    if (!text.trim()) return;
    this.live.append(h("p", {}, text.trim()));
    while (this.live.childElementCount > 6)
      this.live.firstElementChild?.remove();
  }

  // ---- rendering ----

  private setBusy(busy: boolean): void {
    this.sendButton.replaceChildren(icon(busy ? icons.stop : icons.send));
    this.sendButton.setAttribute(
      "aria-label",
      busy ? "Stop answering" : "Send",
    );
    this.log.setAttribute("aria-busy", String(busy));
  }

  private renderAll(): void {
    const nodes: Node[] = [this.renderGreeting()];
    for (const m of this.messages) nodes.push(this.renderMessage(m));
    this.log.replaceChildren(...nodes);
    this.applyConfig();
  }

  private renderGreeting(): HTMLElement {
    const c = this.config;
    const wrap = h("div", { class: "msg assistant greeting" });
    if (!this.ready) {
      wrap.append(h("div", { class: "bubble" }, typing()));
      return wrap;
    }
    if (this.configError) {
      wrap.append(h("div", { class: "bubble" }, h("p", {}, this.configError)));
      return wrap;
    }
    wrap.append(h("div", { class: "bubble" }, renderText(c.greeting)));
    if (!this.messages.length && c.suggestions.length) {
      const chips = h("div", {
        class: "chips",
        role: "group",
        "aria-label": "Suggested questions",
      });
      for (const s of c.suggestions.slice(0, 4)) {
        chips.append(
          h(
            "button",
            { type: "button", class: "chip", onclick: () => void this.send(s) },
            s,
          ),
        );
      }
      wrap.append(chips);
    }
    return wrap;
  }

  private renderMessage(m: Message): HTMLElement {
    const el = h("div", {
      class: `msg ${m.role}${m.status === "error" ? " error" : ""}`,
      "data-id": m.id,
    });
    if (m.role === "user") {
      el.append(h("div", { class: "bubble" }, h("p", {}, m.text)));
      return el;
    }
    const bubble = h("div", { class: "bubble" });
    if (m.text) bubble.append(renderText(m.text));
    else if (m.status === "streaming") bubble.append(typing());
    if (m.status === "error") {
      bubble.append(h("p", {}, m.error ?? "Something went wrong."));
    }
    if (m.text || m.status !== "stopped") el.append(bubble);
    if (m.status === "stopped")
      el.append(
        h(
          "p",
          { class: "stopped" },
          m.text ? "Stopped." : "Stopped before answering.",
        ),
      );
    if (m.notice) el.append(h("p", { class: "notice" }, m.notice));
    if (m.status !== "streaming") {
      const sources = this.config.show_sources
        ? renderSources(
            m.citations,
            this.config.source_label,
            `${this.uid}-${m.id}`,
          )
        : renderLinks(relatedLinks(m.citations, this.config.page_links));
      if (sources) el.append(sources);
      if (m.booking) el.append(this.renderBooking(m.booking, !m.answered));
      else if (m.choices && !m.answered && m.choices.options.length) {
        el.append(this.renderChoices(m.choices, `${this.uid}-${m.id}-choices`));
      }
    }
    const actions = h("div", { class: "actions" });
    if (m.status === "done" && m.handoff && this.config.handoff_url) {
      actions.append(
        h(
          "a",
          { class: "handoff", href: this.config.handoff_url, target: "_top" },
          icon(icons.person),
          this.config.handoff_text,
        ),
      );
    }
    if (m.status === "error" && m.retry) {
      const question = m.retry;
      actions.append(
        h(
          "button",
          {
            type: "button",
            class: "retry",
            onclick: () => {
              this.messages = this.messages.filter((x) => x !== m);
              // Drop the question too; send() adds it again.
              const last = this.messages[this.messages.length - 1];
              if (last?.role === "user" && last.text === question)
                this.messages.pop();
              void this.send(question);
            },
          },
          "Try again",
        ),
      );
    }
    if (actions.childElementCount) el.append(actions);
    return el;
  }

  private renderChoices(c: Choices, id: string): HTMLElement {
    const list = h("div", { class: "choice-list" });
    for (const o of c.options) {
      const text =
        c.kind === "slot"
          ? `${o.label}, ${c.label.replace(/^Open times, /, "")}`
          : o.label;
      list.append(
        h(
          "button",
          {
            type: "button",
            class: `choice ${c.kind}`,
            "aria-label": o.detail ? `${o.label}, ${o.detail}` : undefined,
            onclick: () => this.tap(text, { type: c.kind, id: o.id }),
          },
          h("span", { class: "choice-label" }, o.label),
          o.detail
            ? h(
                "span",
                { class: "choice-detail", "aria-hidden": "true" },
                o.detail,
              )
            : null,
        ),
      );
    }
    return h(
      "div",
      { class: "choices", role: "group", "aria-labelledby": id },
      h("p", { class: "choices-label", id }, c.label),
      list,
    );
  }

  private renderBooking(b: BookingSummary, active: boolean): HTMLElement {
    const pending = b.status === "pending";
    const rows: [string, string | null | undefined][] = [
      ["Service", b.price ? `${b.service}, ${b.price}` : b.service],
      ["When", b.when],
      ["With", b.staff],
      ["Name", b.name],
      ["Email", b.contact],
      ["Reference", b.reference],
    ];
    const list = h("dl", { class: "booking-list" });
    for (const [label, value] of rows) {
      if (value)
        list.append(
          h(
            "div",
            { class: "booking-row" },
            h("dt", {}, label),
            h("dd", {}, value),
          ),
        );
    }
    const card = h(
      "div",
      {
        class: `booking ${b.status}`,
        role: "group",
        "aria-label": pending ? "Booking to confirm" : "Booking confirmed",
      },
      h(
        "p",
        { class: "booking-head" },
        pending ? null : icon(icons.check),
        pending ? (active ? "Check the details" : "Booking details") : "Booked",
      ),
      list,
    );
    if (pending && active) {
      card.append(
        h(
          "div",
          { class: "booking-actions" },
          h(
            "button",
            {
              type: "button",
              class: "confirm",
              onclick: () => this.tap("Book it", { type: "confirm" }),
            },
            "Book it",
          ),
          h(
            "button",
            {
              type: "button",
              class: "change",
              onclick: () => this.tap("Pick another time", { type: "change" }),
            },
            "Pick another time",
          ),
        ),
      );
    }
    return card;
  }

  /** A choice or card button: send it, and keep keyboard focus in the conversation. */
  private tap(text: string, action: BookingAction): void {
    if (this.controller) return;
    void this.send(text, action);
    this.log.focus({ preventScroll: true });
  }

  private updateMessage(m: Message): void {
    const current = this.log.querySelector(`[data-id="${m.id}"]`);
    const next = this.renderMessage(m);
    if (current) current.replaceWith(next);
    else this.log.append(next);
    // Hide suggestion chips once the conversation has started.
    this.log.querySelector(".greeting .chips")?.remove();
  }

  private scrollToEnd(force: boolean): void {
    const log = this.log;
    const nearBottom =
      log.scrollHeight - log.scrollTop - log.clientHeight < 120;
    if (force || nearBottom) log.scrollTop = log.scrollHeight;
  }

  private autosize(): void {
    this.input.style.height = "auto";
    this.input.style.height = `${Math.min(this.input.scrollHeight, 120)}px`;
  }
}

function bookingSentence(b: BookingSummary): string {
  const who = b.staff ? ` with ${b.staff}` : "";
  return b.status === "pending"
    ? `Please confirm: ${b.service}, ${b.when}${who}, for ${b.name}. Use the Book it button to confirm.`
    : `Booked: ${b.service}, ${b.when}${who}.${b.reference ? ` Reference ${b.reference}.` : ""}`;
}

function typing(): HTMLElement {
  return h(
    "span",
    { class: "typing", role: "img", "aria-label": "Typing" },
    h("span"),
    h("span"),
    h("span"),
  );
}
