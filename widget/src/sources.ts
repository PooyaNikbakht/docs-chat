import { h, icon } from "./dom";
import { icons } from "./icons";
import type { Citation, PageLink } from "./types";

export interface Source {
  page: number;
  quote: string;
  context: string;
}

/** One source per page, in the order the answer first cites them. */
export function groupSources(citations: Citation[]): Source[] {
  const byPage = new Map<number, Source>();
  for (const c of citations) {
    if (!byPage.has(c.page)) {
      byPage.set(c.page, {
        page: c.page,
        quote: c.quote,
        context: c.context || c.quote,
      });
    }
  }
  return [...byPage.values()];
}

export function sourceLabel(label: string, page: number): string {
  return `${label}, p. ${page}`;
}

/** The passage with the cited quote wrapped in <mark>. Matching ignores whitespace differences. */
export function highlight(context: string, quote: string): DocumentFragment {
  const fragment = document.createDocumentFragment();
  const words = quote.trim().split(/\s+/).filter(Boolean);
  const pattern = words.length
    ? new RegExp(
        words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("\\s+"),
      )
    : null;
  const match = pattern ? pattern.exec(context) : null;
  if (!match) {
    fragment.append(document.createTextNode(context));
    return fragment;
  }
  const before = context.slice(0, match.index);
  const after = context.slice(match.index + match[0].length);
  if (before) fragment.append(document.createTextNode(before));
  fragment.append(h("mark", {}, match[0]));
  if (after) fragment.append(document.createTextNode(after));
  return fragment;
}

/**
 * Source chips under an answer. Each chip is a button that expands the quoted passage
 * below the row.
 */
export function renderSources(
  citations: Citation[],
  label: string,
  idPrefix: string,
): HTMLElement | null {
  const sources = groupSources(citations);
  if (!sources.length) return null;
  const list = h("ul", { class: "sources", "aria-label": "Sources" });
  const panels = h("div", { class: "passages" });
  sources.forEach((source, i) => {
    const panelId = `${idPrefix}-src-${i}`;
    const panel = h(
      "blockquote",
      { class: "passage", id: panelId, hidden: true },
      h("p", { class: "passage-label" }, sourceLabel(label, source.page)),
      h(
        "p",
        { class: "passage-text" },
        highlight(source.context, source.quote),
      ),
    );
    const button = h(
      "button",
      {
        type: "button",
        class: "chip-source",
        "aria-expanded": "false",
        "aria-controls": panelId,
        onclick: () => {
          const open = button.getAttribute("aria-expanded") !== "true";
          for (const other of list.querySelectorAll("button"))
            other.setAttribute("aria-expanded", "false");
          for (const p of panels.children) (p as HTMLElement).hidden = true;
          button.setAttribute("aria-expanded", String(open));
          panel.hidden = !open;
          if (open)
            panel.scrollIntoView?.({ block: "nearest", behavior: "smooth" });
        },
      },
      icon(icons.doc),
      h("span", {}, sourceLabel(label, source.page)),
      h("span", { class: "chev" }, icon(icons.chevron)),
    );
    list.append(h("li", {}, button));
    panels.append(panel);
  });
  return h("div", { class: "source-block" }, list, panels);
}

/** The site pages for the help center pages an answer cites, once each, in citation order. */
export function relatedLinks(
  citations: Citation[],
  links: PageLink[],
): PageLink[] {
  const seen = new Set<string>();
  const out: PageLink[] = [];
  for (const source of groupSources(citations)) {
    const link = links.find((l) => l.page === source.page);
    if (link && /^(https?:\/\/|\/)/.test(link.url) && !seen.has(link.url)) {
      seen.add(link.url);
      out.push(link);
    }
  }
  return out;
}

/** Links to the business's own pages under an answer, in place of help center references. */
export function renderLinks(links: PageLink[]): HTMLElement | null {
  if (!links.length) return null;
  const list = h("ul", { class: "sources", "aria-label": "Related pages" });
  for (const link of links) {
    list.append(
      h(
        "li",
        {},
        h(
          "a",
          { class: "chip-link", href: link.url, target: "_top" },
          h("span", {}, link.label),
          h("span", { "aria-hidden": "true" }, "\u2192"),
        ),
      ),
    );
  }
  return h("div", { class: "source-block" }, list);
}
