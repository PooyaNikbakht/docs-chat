import Link from "next/link";
import { BrewIcon } from "@/components/northwind/art";
import { BeanPattern, Photo, type PhotoName } from "@/components/northwind/Photo";
import { CafeCard, CoffeeCard, Container, Eyebrow, HelpBand } from "@/components/northwind/ui";
import { money, nw } from "@/data/northwind";

const FEATURED = ["harbour-blend", "first-light", "night-shift"];

const GALLERY: { name: PhotoName; alt: string }[] = [
  { name: "gallery-latte", alt: "A latte with a fern of foam art on a sunlit café table" },
  { name: "gallery-chemex", alt: "Water poured from a kettle into a glass pour-over brewer beside a potted plant" },
  { name: "gallery-flight", alt: "Eight cups of coffee, from black to milky, arranged in a circle on a wooden tray" },
  { name: "gallery-portafilters", alt: "Ground coffee, whole beans and a latte laid out on wooden boards" },
  { name: "gallery-cappuccino", alt: "A cappuccino with a heart in the foam on a dark table" },
];

export default function HomePage() {
  const { business: b, shipping: ship, subscriptions: sub, coffee_notes: notes } = nw;
  const featured = FEATURED.map((id) => nw.coffees.find((c) => c.id === id)!);
  const city = b.city.split(",")[0];
  const roasterName = b.roaster.match(/we call (.+)$/)?.[1] ?? "our roaster";

  const process: { name: PhotoName; alt: string; title: string; body: string }[] = [
    {
      name: "process-drying",
      alt: "Green coffee drying in the sun on a wide patio, with full sacks and mountains behind",
      title: "Sourced with care",
      body: "We buy green coffee from importers who pay producers above the Fairtrade minimum, and publish the price.",
    },
    {
      name: "process-roast",
      alt: "Freshly roasted beans pouring out of a drum roaster into the cooling tray",
      title: `Roasted on ${roasterName}`,
      body: `Every batch goes through ${b.roaster.replace(/ we call .+$/, "")}, ${ship.roast_days}.`,
    },
    {
      name: "process-cool",
      alt: "Roasted coffee beans turning in a roaster's cooling tray",
      title: "Roasted to order",
      body: "Your bag is roasted after you order it, and the roast date is printed on every bag.",
    },
    {
      name: "process-cupping",
      alt: "Three small cups on a wooden table: a latte, an espresso and whole beans",
      title: "Best within a month",
      body: notes.freshness.split(". ").slice(1).join(". "),
    },
  ];

  return (
    <>
      <section aria-labelledby="hero-title" className="relative isolate overflow-hidden bg-espresso text-cream">
        <Photo
          name="hero-roaster"
          alt="A roaster tipping freshly roasted coffee beans into the cooling tray of a drum roaster, lit by a desk lamp"
          sizes="100vw"
          position="62% 55%"
          preload
          className="-z-10"
        />
        {/* Solid scrim, no gradient: keeps the headline above 4.5:1 on any part of the photo. */}
        <div aria-hidden="true" className="absolute inset-0 -z-10 bg-espresso/75 sm:bg-espresso/70" />
        <Container className="flex min-h-[560px] flex-col justify-end pb-12 pt-24 sm:min-h-[620px] sm:pb-16 lg:min-h-[680px] lg:justify-center lg:pb-20">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-oat">
              Roasting in {city} since {b.founded}
            </p>
            <h1 id="hero-title" className="mt-4 font-display text-[44px] font-semibold leading-[1.02] tracking-tight sm:text-6xl lg:text-[72px]">
              {b.tagline.replace(/\.$/, "")}.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-cream">
              We roast to order {ship.roast_days} and ship across Canada and the US. Shipping is free in Canada on orders
              over {money(ship.free_canada_over)}.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/shop"
                className="inline-flex min-h-12 items-center justify-center rounded-full bg-cream px-6 text-[15px] font-semibold text-espresso transition-colors hover:bg-oat"
              >
                Shop coffee
              </Link>
              <Link
                href="/subscriptions"
                className="inline-flex min-h-12 items-center justify-center rounded-full border border-cream/80 px-6 text-[15px] font-semibold text-cream transition-colors hover:bg-cream hover:text-espresso"
              >
                Start a subscription
              </Link>
            </div>
          </div>
        </Container>
      </section>

      <section aria-label="Why Northwind" className="relative overflow-hidden border-b border-line bg-oat">
        <BeanPattern className="text-roast/[0.08]" />
        <Container className="relative grid gap-6 py-8 sm:grid-cols-3 sm:gap-8">
          {[
            ["Roasted to order", `Every bag is roasted ${ship.roast_days} and shows its roast date.`],
            ["Free shipping", `On orders over ${money(ship.free_canada_over)} in Canada and ${money(ship.free_us_over)} to the US.`],
            [`Subscribers save ${sub.discount_percent}%`, "Pause, skip or cancel any time from your account."],
          ].map(([title, body]) => (
            <div key={title} className="flex gap-4">
              <span aria-hidden="true" className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-crema" />
              <div>
                <h2 className="font-display text-xl font-semibold">{title}</h2>
                <p className="mt-1 text-[15px] leading-relaxed text-roast">{body}</p>
              </div>
            </div>
          ))}
        </Container>
      </section>

      <section aria-labelledby="process-title">
        <Container className="py-16 sm:py-24">
          <div className="max-w-2xl">
            <Eyebrow>From green bean to your cup</Eyebrow>
            <h2 id="process-title" className="mt-3 font-display text-4xl font-semibold tracking-tight">
              How a bag of Northwind is made
            </h2>
          </div>
          <ol className="mt-10 grid grid-cols-2 gap-x-4 gap-y-8 sm:gap-6 lg:grid-cols-4">
            {process.map((step, i) => (
              <li key={step.name} className="flex flex-col">
                <div className="relative aspect-[4/5] overflow-hidden rounded-2xl bg-oat">
                  <Photo name={step.name} alt={step.alt} sizes="(min-width: 1152px) 266px, (min-width: 1024px) 23vw, 46vw" />
                  <span
                    aria-hidden="true"
                    className="absolute left-2.5 top-2.5 flex h-8 w-8 sm:left-3 sm:top-3 sm:h-9 sm:w-9 items-center justify-center rounded-full bg-paper font-display text-lg font-semibold text-espresso"
                  >
                    {i + 1}
                  </span>
                </div>
                <h3 className="mt-4 font-display text-lg font-semibold leading-snug sm:text-xl">{step.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-roast sm:text-[15px]">{step.body}</p>
              </li>
            ))}
          </ol>
        </Container>
      </section>

      <section aria-labelledby="coffees-title" className="border-t border-line bg-paper">
        <Container className="py-16 sm:py-24">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <Eyebrow>On the roaster this week</Eyebrow>
              <h2 id="coffees-title" className="mt-3 font-display text-4xl font-semibold tracking-tight">
                Our coffees
              </h2>
            </div>
            <Link href="/shop" className="text-[15px] font-semibold text-green underline underline-offset-4 hover:text-espresso">
              See all {nw.coffees.length} coffees
            </Link>
          </div>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {featured.map((c) => (
              <CoffeeCard key={c.id} coffee={c} compact />
            ))}
          </div>
        </Container>
      </section>

      <section aria-labelledby="sub-title" className="bg-espresso text-cream">
        <div className="grid lg:grid-cols-2">
          <div className="relative aspect-[4/3] sm:aspect-[16/10] lg:order-2 lg:aspect-auto lg:min-h-[560px]">
            <Photo
              name="sub-press"
              alt="Steam rising from a mug next to a French press on a kitchen counter"
              sizes="(min-width: 1024px) 50vw, 100vw"
            />
          </div>
          <div className="px-4 py-14 sm:px-6 sm:py-16 lg:py-20 lg:pl-[max(1.5rem,calc((100vw-72rem)/2+1.5rem))] lg:pr-14">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-crema">Subscriptions</p>
            <h2 id="sub-title" className="mt-3 font-display text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
              Fresh coffee {sub.frequencies}, on your schedule.
            </h2>
            <ul className="mt-8 space-y-3 text-[17px]">
              {[
                `Save ${sub.discount_percent}% on every bag`,
                "Free shipping anywhere in Canada",
                `Pause for up to ${sub.pause_max}, skip a delivery, or cancel any time`,
              ].map((item) => (
                <li key={item} className="flex gap-3">
                  <svg className="mt-1 shrink-0 text-crema" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="m5 12 5 5L20 7" />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
            <div className="mt-9">
              <Link
                href="/subscriptions"
                className="inline-flex min-h-12 items-center rounded-full bg-cream px-6 text-[15px] font-semibold text-espresso hover:bg-oat"
              >
                How subscriptions work
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section aria-labelledby="brew-title">
        <Container className="py-16 sm:py-24">
          <Eyebrow>Brew better at home</Eyebrow>
          <h2 id="brew-title" className="mt-3 font-display text-4xl font-semibold tracking-tight">
            Three ratios worth knowing
          </h2>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {nw.brewing.map((m) => (
              <Link
                key={m.method}
                href="/brew-guides"
                className="group flex items-center gap-5 rounded-2xl border border-line bg-paper p-5 hover:border-espresso"
              >
                <BrewIcon method={m.method} className="h-20 w-20 shrink-0" />
                <div>
                  <h3 className="font-display text-xl font-semibold group-hover:underline">{m.method}</h3>
                  <p className="mt-1 text-sm text-roast">
                    {m.ratio} · {m.dose} for {m.yield}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </Container>
      </section>

      <section aria-labelledby="cafes-title" className="border-t border-line bg-oat/60">
        <Container className="py-16 sm:py-24">
          <Eyebrow>Visit us</Eyebrow>
          <h2 id="cafes-title" className="mt-3 font-display text-4xl font-semibold tracking-tight">
            Our cafés
          </h2>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {nw.cafes.map((c) => (
              <CafeCard key={c.name} cafe={c} />
            ))}
          </div>
        </Container>
      </section>

      <section aria-labelledby="gallery-title">
        <Container className="py-16 sm:py-24">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <Eyebrow>From our cafés</Eyebrow>
              <h2 id="gallery-title" className="mt-3 font-display text-4xl font-semibold tracking-tight">
                A slow cup, any time of day
              </h2>
            </div>
            <p className="max-w-sm text-[15px] text-roast">{nw.cafe_notes.wifi} {nw.cafe_notes.pets}</p>
          </div>
          <ul className="mt-10 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
            {GALLERY.map((g, i) => (
              <li
                key={g.name}
                className={`relative aspect-square overflow-hidden rounded-2xl bg-oat ${i === 0 ? "col-span-2 row-span-2" : ""}`}
              >
                <Photo
                  name={g.name}
                  alt={g.alt}
                  sizes={i === 0 ? "(min-width: 1152px) 552px, (min-width: 1024px) 48vw, calc(100vw - 32px)" : "(min-width: 1152px) 270px, (min-width: 1024px) 24vw, 46vw"}
                />
              </li>
            ))}
          </ul>
        </Container>
      </section>

      <HelpBand title="Questions about an order?">
        Our help assistant answers from our help center any time: shipping, returns, subscriptions and
        brewing. If it doesn&apos;t know, it will tell you and put you in touch with our team.
      </HelpBand>
    </>
  );
}

