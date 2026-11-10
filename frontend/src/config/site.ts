// Single place for personal links and deploy URLs.
const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010").replace(/\/+$/, "");

export const site = {
  productName: "Website support bot",
  author: "Pooya Nikbakht",
  githubUrl: "https://github.com/PooyaNikbakht",
  /** Empty hides the code links. */
  repoUrl: "https://github.com/PooyaNikbakht/docs-chat" as string,
  portfolioUrl: "https://pooya.website",
  /** Where the footer line "Fictional business. Demo by ..." links to. */
  creditUrl: process.env.NEXT_PUBLIC_CREDIT_URL ?? "https://pooya.website",
  /** Where the widget script and sample site are served from in production. */
  publicUrl: "https://coffee.pooya.website",
  /** The FastAPI backend. Inlined into the browser bundle at build time. */
  apiUrl,
  /** The API URL shown in the install snippet. */
  publicApiUrl: "https://api.pooya.website",
  botId: "northwind",
} as const;

/** The exact snippet a client pastes into their site. */
export function installSnippet(bot: string = site.botId): string {
  return `<script src="${site.publicUrl}/embed/widget.js" data-bot="${bot}" data-api="${site.publicApiUrl}" defer></script>`;
}
