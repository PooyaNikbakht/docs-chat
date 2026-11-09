import { optionsFromScript } from "./config";
import type { WidgetOptions } from "./types";
import { Widget } from "./widget";

export interface DocsChatApi {
  /** Mount a widget. Options default to the right-hand corner and the current origin's API. */
  mount(options: Partial<WidgetOptions> & ({ bot: string } | { document: string })): Widget;
  /** Open the first mounted widget's panel, for "Ask a question" buttons on the host page. */
  open(): void;
  /** Remove every mounted widget. */
  destroyAll(): void;
}

declare global {
  interface Window {
    DocsChat?: DocsChatApi;
  }
}

const instances = new Set<Widget>();

function whenBodyReady(run: () => void): void {
  if (document.body) run();
  else document.addEventListener("DOMContentLoaded", run, { once: true });
}

function mount(options: Partial<WidgetOptions> & ({ bot: string } | { document: string })): Widget {
  const full: WidgetOptions = {
    api: location.origin,
    position: "right",
    open: false,
    overrides: {},
    ...options,
  };
  full.api = full.api.replace(/\/+$/, "");
  const widget = new Widget(full);
  instances.add(widget);
  whenBodyReady(() => widget.mount());
  return widget;
}

const api: DocsChatApi = {
  mount,
  open() {
    instances.values().next().value?.open();
  },
  destroyAll() {
    for (const w of instances) w.destroy();
    instances.clear();
  },
};

if (!window.DocsChat) window.DocsChat = api;

// Auto-mount from the script tag: <script src=".../widget.js" data-bot="northwind" data-api="...">
const script = document.currentScript as HTMLScriptElement | null;
if (script && (script.dataset.bot || script.dataset.document)) {
  const options = optionsFromScript(script);
  const key = options.bot ? `bot:${options.bot}` : `doc:${options.document}`;
  // A second copy of the snippet on the same page shouldn't add a second bubble.
  if (!document.querySelector(`docs-chat-widget[data-target="${CSS.escape(key)}"]`)) {
    window.DocsChat.mount(options as WidgetOptions & { bot: string });
  }
}
