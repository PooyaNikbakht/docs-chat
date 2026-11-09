import { h } from "./dom";

/** Inline **bold** only; everything else is plain text. */
function inline(text: string): (Node | string)[] {
  const out: (Node | string)[] = [];
  const parts = text.split(/\*\*(.+?)\*\*/g);
  parts.forEach((part, i) => {
    if (!part) return;
    out.push(i % 2 ? h("strong", {}, part) : part);
  });
  return out;
}

const BULLET = /^\s*(?:[-*•]|\d+[.)])\s+/;

/**
 * Render an answer: paragraphs, and "- " or "1. " lines as lists. Built with DOM nodes,
 * never innerHTML, so model output can't inject markup.
 */
export function renderText(text: string): DocumentFragment {
  const fragment = document.createDocumentFragment();
  const blocks = text.trim().split(/\n{2,}/);
  for (const block of blocks) {
    const lines = block.split("\n").filter((l) => l.trim());
    if (!lines.length) continue;
    let paragraph: string[] = [];
    let list: HTMLElement | null = null;
    const flushParagraph = () => {
      if (paragraph.length) fragment.append(h("p", {}, ...inline(paragraph.join(" "))));
      paragraph = [];
    };
    for (const line of lines) {
      if (BULLET.test(line)) {
        flushParagraph();
        if (!list) {
          list = /^\s*\d/.test(line) ? h("ol") : h("ul");
          fragment.append(list);
        }
        list.append(h("li", {}, ...inline(line.replace(BULLET, ""))));
      } else {
        list = null;
        paragraph.push(line.trim());
      }
    }
    flushParagraph();
  }
  return fragment;
}
