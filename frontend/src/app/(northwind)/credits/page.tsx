import type { Metadata } from "next";
import { Container, PageIntro } from "@/components/northwind/ui";
import { PHOTO_CREDITS, PHOTO_EDITS } from "@/data/photo-credits";

export const metadata: Metadata = { title: "Photo credits" };

export default function CreditsPage() {
  return (
    <>
      <PageIntro eyebrow="Photo credits" title="The photographers behind this site">
        <p>
          Every photo here comes from Unsplash and is used under the{" "}
          <a className="font-medium text-green underline underline-offset-4" href="https://unsplash.com/license">
            Unsplash License
          </a>
          , which allows free commercial use and edits. Thank you to each photographer.
        </p>
      </PageIntro>
      <Container className="py-14 sm:py-20">
        <p className="max-w-3xl text-[15px] leading-relaxed text-roast">
          <span className="font-semibold text-espresso">Edits: </span>
          {PHOTO_EDITS}
        </p>
        <ul className="mt-8 divide-y divide-line border-y border-line">
          {PHOTO_CREDITS.map((c) => (
            <li key={c.url} className="grid gap-1 py-4 sm:grid-cols-[220px_1fr_auto] sm:items-baseline sm:gap-6">
              <p className="font-semibold">{c.photographer}</p>
              <p className="break-words text-sm text-roast">Used as: {c.files.join(", ")}</p>
              <a className="text-sm font-medium text-green underline underline-offset-4" href={c.url}>
                View on Unsplash<span className="sr-only"> (photo by {c.photographer})</span>
              </a>
            </li>
          ))}
        </ul>
      </Container>
    </>
  );
}
