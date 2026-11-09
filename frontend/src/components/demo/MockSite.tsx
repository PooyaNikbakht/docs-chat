import type { DocumentInfo } from "@/lib/types";

/** A plain, generic website for the uploaded document's bot to sit on. */
export function MockSite({ doc, onReset }: { doc: DocumentInfo; onReset: () => void }) {
  return (
    <div className="flex flex-1 flex-col">
      <div className="border-b border-line bg-accent-soft">
        <div className="mx-auto flex max-w-5xl flex-col items-start gap-3 px-4 py-4 sm:px-6">
          <p className="text-sm leading-relaxed text-ink" role="status">
            <span className="font-semibold">Your bot is live on this mock page.</span> It answers from{" "}
            <span className="font-mono text-[13px]">{doc.name}</span> ({doc.pages} {doc.pages === 1 ? "page" : "pages"}).
            Open the chat in the corner and ask it something.
          </p>
          <button
            type="button"
            onClick={onReset}
            className="inline-flex min-h-10 items-center justify-center rounded-[8px] border border-line bg-background px-4 text-sm font-medium text-ink hover:border-accent"
          >
            Upload a different PDF
          </button>
        </div>
      </div>

      <div className="mx-auto w-full max-w-5xl flex-1 px-4 py-10 sm:px-6">
        <div className="flex items-center justify-between border-b border-line pb-5">
          <div className="flex items-center gap-2.5">
            <span aria-hidden="true" className="h-7 w-7 rounded-full bg-ink/80" />
            <span className="text-base font-semibold text-ink">Your business</span>
          </div>
          <div aria-hidden="true" className="hidden gap-6 sm:flex">
            {[64, 72, 56, 60].map((w, i) => (
              <span key={i} className="h-2.5 rounded-full bg-line" style={{ width: w }} />
            ))}
          </div>
        </div>

        <div className="grid gap-10 py-12 md:grid-cols-[1.2fr_1fr] md:items-center">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">Your website goes here</h1>
            <p className="mt-4 max-w-md text-base leading-relaxed text-muted">
              This stand-in page shows how the support bot sits on your site. Visitors open it from the corner,
              ask in their own words, and get an answer with the page it came from.
            </p>
            <div aria-hidden="true" className="mt-6 flex gap-3">
              <span className="h-11 w-32 rounded-[8px] bg-ink/80" />
              <span className="h-11 w-28 rounded-[8px] border border-line" />
            </div>
          </div>
          <div aria-hidden="true" className="aspect-[4/3] rounded-[8px] border border-line bg-surface" />
        </div>

        <div aria-hidden="true" className="grid gap-4 sm:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="rounded-[8px] border border-line p-5">
              <span className="block h-3 w-24 rounded-full bg-line" />
              <span className="mt-4 block h-2 w-full rounded-full bg-surface" />
              <span className="mt-2 block h-2 w-5/6 rounded-full bg-surface" />
              <span className="mt-2 block h-2 w-2/3 rounded-full bg-surface" />
            </div>
          ))}
        </div>

        <section id="contact" className="mt-12 rounded-[8px] border border-line p-6">
          <h2 className="text-lg font-semibold text-ink">Contact</h2>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            The bot&apos;s &quot;Talk to a human&quot; link points here. On your site it would go to your contact page,
            an email address or a booking link.
          </p>
        </section>
      </div>
    </div>
  );
}
