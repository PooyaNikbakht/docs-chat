import { describe, expect, it } from "vitest";
import { mergeConfig, onAccent, optionsFromScript } from "../src/config";
import { renderText } from "../src/markdown";

describe("config", () => {
  it("reads options from data attributes", () => {
    const s = document.createElement("script");
    s.src = "https://bot.example/embed/widget.js";
    Object.assign(s.dataset, {
      bot: "northwind",
      api: "https://api.example/",
      accent: "#5E7A5A",
      suggestions: "One? | Two?",
      tooltip: "false",
      position: "left",
    });
    const o = optionsFromScript(s);
    expect(o).toMatchObject({ api: "https://api.example", bot: "northwind", position: "left", open: false });
    expect(o.overrides).toEqual({ accent_color: "#5E7A5A", suggestions: ["One?", "Two?"], tooltip: null });
  });

  it("defaults the API to the script's origin", () => {
    const s = document.createElement("script");
    s.src = "https://bot.example/embed/widget.js";
    s.dataset.bot = "x";
    expect(optionsFromScript(s).api).toBe("https://bot.example");
  });

  it("lets data attributes win over server config, and rejects bad colours", () => {
    const c = mergeConfig({ name: "Server", accent_color: "#3B2A20" }, { name: "Local" });
    expect(c.name).toBe("Local");
    expect(c.accent_color).toBe("#3B2A20");
    expect(mergeConfig({ accent_color: "red; background: url(x)" }, {}).accent_color).toBe("#0F766E");
  });

  it("picks readable text for the accent", () => {
    expect(onAccent("#3B2A20")).toBe("#FFFFFF");
    expect(onAccent("#F7E9C8")).toBe("#111111");
  });
});

describe("answer text", () => {
  it("renders paragraphs, lists and bold without HTML injection", () => {
    const div = document.createElement("div");
    div.append(renderText("We ship to:\n- **Canada**\n- the US\n\n<b>Thanks</b>"));
    expect(div.querySelectorAll("li")).toHaveLength(2);
    expect(div.querySelector("strong")?.textContent).toBe("Canada");
    expect(div.querySelector("b")).toBeNull();
    expect(div.textContent).toContain("<b>Thanks</b>");
  });
});
