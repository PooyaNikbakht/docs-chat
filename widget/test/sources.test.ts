import { describe, expect, it } from "vitest";
import {
  groupSources,
  highlight,
  relatedLinks,
  renderSources,
} from "../src/sources";
import type { Citation, PageLink } from "../src/types";

const cite = (
  index: number,
  page: number,
  quote: string,
  context = `Before. ${quote} After.`,
): Citation => ({
  index,
  chunk_id: `c${page}`,
  page,
  quote,
  context,
});

describe("citation rendering", () => {
  it("groups citations into one source per page, in order of first use", () => {
    const sources = groupSources([
      cite(1, 4, "Pause up to 3 months."),
      cite(2, 2, "Ships free."),
      cite(3, 4, "Skip a delivery."),
    ]);
    expect(sources.map((s) => s.page)).toEqual([4, 2]);
    expect(sources[0].quote).toBe("Pause up to 3 months.");
  });

  it("renders a chip per page with the label and page number", () => {
    const el = renderSources(
      [cite(1, 4, "Pause."), cite(2, 9, "Hours.")],
      "Help center",
      "t",
    )!;
    const chips = [...el.querySelectorAll("button.chip-source")];
    expect(chips.map((b) => b.textContent)).toEqual([
      "Help center, p. 4",
      "Help center, p. 9",
    ]);
    expect(
      chips.every((b) => b.getAttribute("aria-expanded") === "false"),
    ).toBe(true);
  });

  it("expands one quoted passage at a time", () => {
    const el = renderSources(
      [cite(1, 4, "Pause."), cite(2, 9, "Hours.")],
      "Help center",
      "t",
    )!;
    const [first, second] =
      el.querySelectorAll<HTMLButtonElement>("button.chip-source");
    const panel = (b: HTMLButtonElement) =>
      el.querySelector<HTMLElement>(`#${b.getAttribute("aria-controls")}`)!;

    first.click();
    expect(first.getAttribute("aria-expanded")).toBe("true");
    expect(panel(first).hidden).toBe(false);
    expect(panel(first).querySelector("mark")?.textContent).toBe("Pause.");

    second.click();
    expect(first.getAttribute("aria-expanded")).toBe("false");
    expect(panel(first).hidden).toBe(true);
    expect(panel(second).hidden).toBe(false);

    second.click();
    expect(panel(second).hidden).toBe(true);
  });

  it("returns nothing when there are no citations", () => {
    expect(renderSources([], "Help center", "t")).toBeNull();
  });

  it("highlights the quote despite whitespace differences", () => {
    const frag = highlight(
      "Intro. You can  pause\nfor 3 months. End.",
      "You can pause for 3 months.",
    );
    const div = document.createElement("div");
    div.append(frag);
    expect(div.querySelector("mark")?.textContent).toBe(
      "You can  pause\nfor 3 months.",
    );
    expect(div.textContent).toBe("Intro. You can  pause\nfor 3 months. End.");
  });

  it("treats passage text as text, never as HTML", () => {
    const evil = '<img src=x onerror="alert(1)">';
    const el = renderSources(
      [cite(1, 1, evil, `See ${evil}`)],
      "Help center",
      "t",
    )!;
    expect(el.querySelector("img")).toBeNull();
    expect(el.querySelector("mark")?.textContent).toBe(evil);
  });
});

describe("relatedLinks", () => {
  const at = (page: number, index = page): Citation => ({
    index,
    chunk_id: `c${page}`,
    page,
    quote: "q",
    context: "q",
  });
  const links: PageLink[] = [
    { page: 4, label: "See subscriptions", url: "/subscriptions" },
    { page: 5, label: "Shop our coffees", url: "https://coffee.example/shop" },
    { page: 6, label: "Shop our coffees", url: "https://coffee.example/shop" },
    { page: 7, label: "Bad link", url: "javascript:alert(1)" },
  ];

  it("maps cited pages to site links, once each, in citation order", () => {
    const out = relatedLinks([at(5), at(6), at(4), at(5, 9)], links);
    expect(out.map((l) => l.label)).toEqual([
      "Shop our coffees",
      "See subscriptions",
    ]);
  });

  it("skips pages without a link and links that aren't http(s) or a path", () => {
    expect(relatedLinks([at(1), at(7)], links)).toEqual([]);
  });
});
