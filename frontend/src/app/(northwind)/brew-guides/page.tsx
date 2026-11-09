import type { Metadata } from "next";
import { BrewIcon } from "@/components/northwind/art";
import { Photo } from "@/components/northwind/Photo";
import { BREW_PHOTOS } from "@/data/photo-map";
import { Container, HelpBand, PageIntro } from "@/components/northwind/ui";
import { nw } from "@/data/northwind";

export const metadata: Metadata = { title: "Brew guides" };

const TIPS: Record<string, string> = {
  "Pour-over": "Bloom with twice the coffee's weight in water for 30 seconds first.",
  "French press": "Stir after one minute, press slowly at four minutes, and pour right away.",
  Espresso: "If a shot runs fast and tastes sour, grind finer. If it runs slow and tastes bitter, grind coarser.",
};

export default function BrewGuidesPage() {
  return (
    <>
      <PageIntro
        eyebrow="Brew guides"
        title="Good coffee at home, by the numbers"
        photo={{ name: "banner-brew", alt: "Water poured from a kettle into a glass pour-over brewer on a kitchen table" }}
      >
        <p>Start with these ratios, then adjust one thing at a time. A kitchen scale helps more than any gadget.</p>
      </PageIntro>

      <Container className="space-y-6 py-14 sm:py-20">
        {nw.brewing.map((m) => (
          <article
            key={m.method}
            className="grid overflow-hidden rounded-3xl border border-line bg-paper md:grid-cols-[minmax(0,300px)_1fr]"
          >
            <div className="relative aspect-[4/3] bg-oat md:aspect-auto md:min-h-[300px]">
              <Photo
                name={BREW_PHOTOS[m.method].name}
                alt={BREW_PHOTOS[m.method].alt}
                sizes="(min-width: 768px) 300px, calc(100vw - 32px)"
              />
            </div>
            <div className="p-6 sm:p-8">
              <div className="flex items-center gap-3">
                <BrewIcon method={m.method} className="h-12 w-12 shrink-0" />
                <h2 className="font-display text-3xl font-semibold tracking-tight">{m.method}</h2>
              </div>
              <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3 lg:grid-cols-5">
                {[
                  ["Ratio", m.ratio],
                  ["Coffee", m.dose],
                  ["Yield", m.yield.replace(" of ", " ")],
                  ["Grind", m.grind],
                  ["Water", m.temperature],
                ].map(([k, v]) => (
                  <div key={k}>
                    <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-green">{k}</dt>
                    <dd className="mt-1 text-[17px] font-medium first-letter:uppercase">{v}</dd>
                  </div>
                ))}
              </dl>
              <p className="mt-5 border-t border-line pt-4 text-[15px] leading-relaxed text-roast">
                Brew for {m.time}. {TIPS[m.method]}
              </p>
            </div>
          </article>
        ))}

        <section className="rounded-3xl bg-sage p-6 sm:p-8">
          <h2 className="font-display text-2xl font-semibold">Storing coffee</h2>
          <p className="mt-2 max-w-3xl text-[16px] leading-relaxed">
            Keep beans in their resealable bag or an airtight container, away from light and heat. Don&apos;t keep
            coffee in the fridge. {nw.coffee_notes.freshness}
          </p>
        </section>
      </Container>

      <HelpBand title="Dialling in a new grinder?">
        Ask our assistant for the ratio, grind and water temperature for your brewer.
      </HelpBand>
    </>
  );
}
