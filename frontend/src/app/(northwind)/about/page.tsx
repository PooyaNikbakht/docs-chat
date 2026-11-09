import type { Metadata } from "next";
import { Origins } from "@/components/northwind/art";
import { Photo } from "@/components/northwind/Photo";
import { Container, Eyebrow, PageIntro } from "@/components/northwind/ui";
import { nw } from "@/data/northwind";

export const metadata: Metadata = { title: "About" };

export default function AboutPage() {
  const { business: b, coffee_notes: notes } = nw;
  const origins = [...new Set(nw.coffees.flatMap((c) => c.origin.split(" and ")))];
  return (
    <>
      <PageIntro
        eyebrow="About us"
        title="A small roaster with a big old drum"
        photo={{ name: "banner-about", alt: "Burlap coffee sacks stacked high against a wall" }}
      >
        <p>
          {b.founders} started {b.short_name} in {b.city} in {b.founded}. We still roast every batch on {b.roaster}
          , and we run {nw.cafes.length} cafés.
        </p>
      </PageIntro>

      <Container className="grid items-center gap-12 py-14 sm:py-20 lg:grid-cols-2">
        <Origins className="h-auto w-full" />
        <div>
          <Eyebrow>Sourcing</Eyebrow>
          <h2 className="mt-3 font-display text-3xl font-semibold tracking-tight">Where our coffee comes from</h2>
          <p className="mt-4 text-[17px] leading-relaxed">{notes.sourcing}</p>
          <ul className="mt-6 flex flex-wrap gap-2" aria-label="Origins">
            {origins.map((o) => (
              <li key={o} className="rounded-full border border-line bg-paper px-3.5 py-1.5 text-sm font-medium">
                {o}
              </li>
            ))}
          </ul>
        </div>
      </Container>

      <section aria-labelledby="roaster-title" className="bg-espresso text-cream">
        <div className="grid md:grid-cols-2">
          <div className="relative aspect-[4/3] w-full md:aspect-auto md:min-h-[520px]">
            <Photo
              name="about-roaster"
              alt="Freshly roasted coffee beans tumbling out of a drum roaster into the cooling tray"
              sizes="(min-width: 768px) 50vw, 100vw"
            />
          </div>
          <div className="flex flex-col justify-center px-4 py-14 sm:px-6 md:pl-12 lg:pl-16 lg:pr-[max(1.5rem,calc((100vw-72rem)/2+1.5rem))]">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-crema">The roastery</p>
            <h2 id="roaster-title" className="mt-3 font-display text-3xl font-semibold tracking-tight sm:text-4xl">
              Every batch on {b.roaster.match(/we call (.+)$/)?.[1] ?? "one roaster"}
            </h2>
            <p className="mt-4 text-[17px] leading-relaxed text-cream/85">
              {b.roaster.match(/we call (.+)$/)?.[1]} is {b.roaster.replace(/ we call .+$/, "")}. {notes.freshness}
            </p>
            <p className="mt-4 text-[17px] leading-relaxed text-cream/85">
              Visit the roastery at {nw.cafes.find((c) => c.name === "Roastery")?.address}.{" "}
              {nw.cafes.find((c) => c.name === "Roastery")?.note}
            </p>
          </div>
        </div>
      </section>

      <section className="border-t border-line bg-paper">
        <Container className="grid gap-10 py-14 sm:py-20 md:grid-cols-3">
          {[
            ["How we roast", notes.roast_levels],
            ["Always fresh", notes.freshness],
            ["Allergens", notes.allergens],
          ].map(([title, body]) => (
            <div key={title}>
              <h2 className="font-display text-2xl font-semibold">{title}</h2>
              <p className="mt-3 text-[15px] leading-relaxed text-roast">{body}</p>
            </div>
          ))}
        </Container>
      </section>
    </>
  );
}
