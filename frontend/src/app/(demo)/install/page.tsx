import Link from "next/link";
import type { Metadata } from "next";
import { CopyButton } from "@/components/demo/CopyButton";
import { installSnippet, site } from "@/config/site";

export const metadata: Metadata = {
  title: "How to install",
  description: "Add the support bot to any website with one script tag. Notes for Shopify, WordPress, Webflow, Squarespace and Google Sites.",
};

const PLATFORMS = [
  {
    name: "Shopify",
    steps: "In your admin, open Online Store, then Themes. Choose Edit code on your theme, open layout/theme.liquid, and paste the snippet just before </body>. Save.",
  },
  {
    name: "WordPress",
    steps: "Paste the snippet into your theme's footer, just before </body>, or use any plugin that adds code to the site footer. On WordPress.com this needs a plan that allows plugins.",
  },
  {
    name: "Webflow",
    steps: "Open Site settings, then Custom code, and paste the snippet into Footer code. Save and publish the site. Custom code needs a paid site plan.",
  },
  {
    name: "Squarespace",
    steps: "Open Settings, then Advanced, then Code Injection, and paste the snippet into Footer. Code injection is available on plans that include it.",
  },
  {
    name: "Google Sites",
    steps: "Choose Insert, then Embed, then Embed code, and paste the snippet. Google Sites runs embeds in a sandboxed frame, so the chat shows inside that box instead of floating over the page. Give the box enough height, or link to a dedicated help page.",
  },
  {
    name: "Any other site",
    steps: "Paste the snippet into your HTML just before </body>. It loads with defer, so it never slows down the rest of the page.",
  },
];

const OPTIONS: [string, string][] = [
  ["data-bot", "Which bot to load. Each bot has its own documents, greeting and colours."],
  ["data-api", "The bot's API address."],
  ["data-accent", 'Override the accent colour, for example "#3B2A20".'],
  ["data-position", '"right" (default) or "left".'],
  ["data-greeting", "Override the greeting message."],
  ["data-suggestions", 'Override the suggested questions, separated by "|".'],
  ["data-handoff-url", "Where \"Talk to a human\" goes: a contact page, a mailto: link or a booking page."],
  ["data-tooltip", 'A one-time hint above the bubble, or "false" to turn it off.'],
  ["data-open", '"true" opens the chat on the first visit of a session.'],
];

const HOW = [
  [
    "Finds the right passages",
    "Your documents are split into short passages and indexed. Each question pulls the few passages that match it best, including the previous question for follow-ups like \"what about the US?\".",
  ],
  [
    "Answers only from them",
    "The model is told to answer from those passages alone, in two to four friendly sentences. It speaks as your business and never adds outside facts.",
  ],
  [
    "Shows its sources",
    "Every answer lists the pages it used. Visitors can open a source to read the exact passage, with the quoted words highlighted.",
  ],
  [
    "Hands off when it doesn't know",
    "If nothing in your documents matches, it says so plainly and offers a \"Talk to a human\" link, instead of guessing. Off-topic questions never reach the model at all.",
  ],
  [
    "Stays within limits",
    "Per-visitor and daily caps keep costs predictable. If a cap is reached or the AI provider is down, the bot switches to a built-in demo mode instead of breaking.",
  ],
  [
    "Keeps your site intact",
    "The widget renders inside a Shadow DOM: your CSS can't break it, and its CSS can't leak into your pages. It is about 10 KB gzipped, with no framework needed on your site.",
  ],
];

export default function InstallPage() {
  const snippet = installSnippet();
  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-12 sm:px-6 sm:py-16">
      <p className="font-mono text-xs uppercase tracking-widest text-accent">How to install</p>
      <h1 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
        One line of code adds the bot to any website
      </h1>
      <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted">
        Paste this snippet into your site, just before the closing <code className="font-mono text-[0.9em]">&lt;/body&gt;</code>{" "}
        tag. The chat bubble appears in the corner, already set up with your documents, greeting and colours.
      </p>

      <section aria-labelledby="snippet-title" className="mt-8 rounded-[8px] border border-line bg-surface">
        <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-2.5">
          <h2 id="snippet-title" className="text-sm font-medium text-ink">
            Embed snippet
          </h2>
          <CopyButton text={snippet} />
        </div>
        <pre className="whitespace-pre-wrap break-all px-4 py-4 font-mono text-[13px] leading-relaxed text-ink">
          <code>{snippet}</code>
        </pre>
      </section>
      <p className="mt-3 text-sm text-muted">
        This is the same snippet the{" "}
        <Link className="text-ink underline underline-offset-4 hover:text-accent" href="/">
          Northwind Coffee demo
        </Link>{" "}
        uses.
      </p>

      <section aria-labelledby="platforms-title" className="mt-14">
        <h2 id="platforms-title" className="text-xl font-semibold tracking-tight text-ink">
          Where to paste it
        </h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {PLATFORMS.map((p) => (
            <article key={p.name} className="rounded-[8px] border border-line p-5">
              <h3 className="font-medium text-ink">{p.name}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{p.steps}</p>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="how-title" className="mt-14">
        <h2 id="how-title" className="text-xl font-semibold tracking-tight text-ink">
          How it works
        </h2>
        <ol className="mt-5 grid gap-x-8 gap-y-6 sm:grid-cols-2">
          {HOW.map(([title, body], i) => (
            <li key={title} className="flex gap-4">
              <span
                aria-hidden="true"
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-line font-mono text-xs text-accent"
              >
                {i + 1}
              </span>
              <div>
                <h3 className="font-medium text-ink">{title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted">{body}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="options-title" className="mt-14">
        <h2 id="options-title" className="text-xl font-semibold tracking-tight text-ink">
          Options
        </h2>
        <p className="mt-2 text-sm text-muted">
          Most settings live with the bot, so the snippet stays short. These attributes override them per site.
        </p>
        <div className="mt-5 overflow-x-auto rounded-[8px] border border-line">
          <table className="w-full min-w-[520px] text-left text-sm">
            <thead className="bg-surface text-ink">
              <tr>
                <th scope="col" className="px-4 py-2.5 font-medium">
                  Attribute
                </th>
                <th scope="col" className="px-4 py-2.5 font-medium">
                  What it does
                </th>
              </tr>
            </thead>
            <tbody>
              {OPTIONS.map(([name, desc]) => (
                <tr key={name} className="border-t border-line">
                  <td className="whitespace-nowrap px-4 py-2.5 font-mono text-[13px] text-accent">{name}</td>
                  <td className="px-4 py-2.5 text-muted">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-labelledby="privacy-title" className="mt-14 rounded-[8px] border border-line p-6">
        <h2 id="privacy-title" className="text-xl font-semibold tracking-tight text-ink">
          Privacy and limits
        </h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-relaxed text-muted">
          <li>API keys stay on the server. The widget only ever talks to the bot&apos;s API.</li>
          <li>Conversations live in the visitor&apos;s browser tab and in server memory for follow-up questions. Nothing is stored in a database.</li>
          <li>The AI providers used don&apos;t train on the questions or documents.</li>
          <li>
            On this public demo, uploads on the{" "}
            <a className="text-ink underline underline-offset-4 hover:text-accent" href="/try">
              try page
            </a>{" "}
            are limited to 5 MB and 25 pages and deleted within an hour, and each visitor gets 10 live answers per
            hour.
          </li>
        </ul>
      </section>

      <section className="mt-14 flex flex-col items-start gap-4 border-t border-line pt-10 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight text-ink">Want this on your website?</h2>
          <p className="mt-1 text-sm text-muted">
            I set it up on your documents, match your brand, and connect the handoff to your inbox or helpdesk.
          </p>
        </div>
        <a
          href={site.portfolioUrl}
          className="inline-flex min-h-11 items-center rounded-[8px] bg-accent px-5 text-sm font-medium text-background hover:opacity-90"
        >
          Get in touch
        </a>
      </section>
    </div>
  );
}
