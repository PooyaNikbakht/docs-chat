import type { BotConfig, WidgetOptions } from "./types";

const HEX = /^#(?:[0-9a-f]{3}|[0-9a-f]{6})$/i;

/** Read widget options from a script tag's data attributes. */
export function optionsFromScript(script: HTMLScriptElement): WidgetOptions {
  const d = script.dataset;
  const overrides: Partial<BotConfig> = {};
  if (d.name) overrides.name = d.name;
  if (d.subline) overrides.subline = d.subline;
  if (d.greeting) overrides.greeting = d.greeting;
  if (d.accent && HEX.test(d.accent)) overrides.accent_color = d.accent;
  if (d.handoffUrl) overrides.handoff_url = d.handoffUrl;
  if (d.handoffText) overrides.handoff_text = d.handoffText;
  if (d.sourceLabel) overrides.source_label = d.sourceLabel;
  if (d.suggestions) overrides.suggestions = d.suggestions.split("|").map((s) => s.trim()).filter(Boolean);
  if (d.tooltip !== undefined) overrides.tooltip = d.tooltip === "false" ? null : d.tooltip;
  return {
    api: (d.api || new URL(script.src, location.href).origin).replace(/\/+$/, ""),
    bot: d.bot || undefined,
    document: d.document || undefined,
    position: d.position === "left" ? "left" : "right",
    open: d.open === "true",
    overrides,
  };
}

export const DEFAULTS: BotConfig = {
  name: "Support",
  subline: "Answers from this site's documents",
  greeting: "Hi! Ask me a question and I'll answer from our documents.",
  suggestions: [],
  accent_color: "#0F766E",
  handoff_text: "Talk to a human",
  handoff_url: "",
  tooltip: null,
  source_label: "Source",
  show_sources: true,
  page_links: [],
  mode: "unknown",
};

/** Data attributes win over the server config, which wins over the defaults. */
export function mergeConfig(server: Partial<BotConfig>, overrides: Partial<BotConfig>): BotConfig {
  const merged = { ...DEFAULTS, ...server, ...overrides };
  if (!HEX.test(merged.accent_color)) merged.accent_color = DEFAULTS.accent_color;
  return merged;
}

/** Black or white text, whichever reads better on the accent colour. */
export function onAccent(hex: string): string {
  let c = hex.replace("#", "");
  if (c.length === 3) c = [...c].map((x) => x + x).join("");
  const [r, g, b] = [0, 2, 4].map((i) => {
    const v = parseInt(c.slice(i, i + 2), 16) / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return luminance > 0.179 ? "#111111" : "#FFFFFF";
}
