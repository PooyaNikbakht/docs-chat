import Link from "next/link";
import { capitalize, listing, money, nw, roastStep, sundayHours, type Cafe, type Coffee } from "@/data/northwind";
import { CAFE_PHOTOS, COFFEE_PHOTOS } from "@/data/photo-map";
import { AskButton } from "./AskButton";
import { CoffeeBag, RoastMeter } from "./art";
import { BeanPattern, Photo, type PhotoName } from "./Photo";

export function Container({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`mx-auto max-w-6xl px-4 sm:px-6 ${className}`}>{children}</div>;
}

export function Eyebrow({ children }: { children: React.ReactNode }) {
  return <p className="text-xs font-semibold uppercase tracking-[0.18em] text-green">{children}</p>;
}

export function PageIntro({
  eyebrow,
  title,
  children,
  photo,
}: {
  eyebrow: string;
  title: string;
  children?: React.ReactNode;
  photo?: { name: PhotoName; alt: string; position?: string };
}) {
  if (!photo) {
    return (
      <section className="border-b border-line">
        <Container className="py-14 sm:py-20">
          <Eyebrow>{eyebrow}</Eyebrow>
          <h1 className="mt-3 max-w-3xl font-display text-4xl font-semibold leading-[1.08] tracking-tight sm:text-[56px]">
            {title}
          </h1>
          {children && <div className="mt-5 max-w-2xl text-lg leading-relaxed text-roast">{children}</div>}
        </Container>
      </section>
    );
  }
  return (
    <section className="border-b border-line">
      <Container className="grid items-center gap-8 py-10 sm:py-14 lg:grid-cols-[1fr_1.05fr] lg:gap-14 lg:py-16">
        <div>
          <Eyebrow>{eyebrow}</Eyebrow>
          <h1 className="mt-3 max-w-xl font-display text-4xl font-semibold leading-[1.08] tracking-tight sm:text-[52px]">
            {title}
          </h1>
          {children && <div className="mt-5 max-w-xl text-lg leading-relaxed text-roast">{children}</div>}
        </div>
        <div className="relative aspect-[16/10] overflow-hidden rounded-3xl bg-oat">
          <Photo
            name={photo.name}
            alt={photo.alt}
            position={photo.position}
            sizes="(min-width: 1152px) 560px, (min-width: 1024px) 50vw, calc(100vw - 32px)"
            preload
          />
        </div>
      </Container>
    </section>
  );
}

const buttonBase =
  "inline-flex min-h-12 items-center justify-center gap-2 rounded-full px-6 text-[15px] font-semibold transition-colors";

export function ButtonLink({
  href,
  children,
  variant = "primary",
}: {
  href: string;
  children: React.ReactNode;
  variant?: "primary" | "outline";
}) {
  const style =
    variant === "primary"
      ? "bg-espresso text-cream hover:bg-roast"
      : "border border-espresso text-espresso hover:bg-espresso hover:text-cream";
  return (
    <Link href={href} className={`${buttonBase} ${style}`}>
      {children}
    </Link>
  );
}

export function CoffeeCard({ coffee, compact = false }: { coffee: Coffee; compact?: boolean }) {
  const shot = COFFEE_PHOTOS[coffee.id];
  return (
    <article className="flex h-full flex-col overflow-hidden rounded-2xl border border-line bg-paper">
      <div className="relative aspect-[4/3] bg-oat">
        {shot ? (
          <Photo name={shot.name} alt={shot.alt} sizes="(min-width: 1152px) 368px, (min-width: 1024px) 31vw, (min-width: 640px) 46vw, calc(100vw - 32px)" />
        ) : (
          <div className="flex h-full items-end justify-center px-6 pb-4 pt-6">
            <CoffeeBag color={coffee.color} className="h-40 w-auto" />
          </div>
        )}
        <span className="absolute left-3 top-3 inline-flex items-center gap-2 rounded-full bg-paper px-3 py-1 text-xs font-semibold text-espresso">
          <span aria-hidden="true" className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: coffee.color }} />
          {coffee.origin}
        </span>
      </div>
      <div className="flex flex-1 flex-col p-5">
        <div className="flex items-start justify-between gap-3">
          <h3 className="font-display text-[22px] font-semibold leading-tight">{coffee.name}</h3>
          <p className="shrink-0 text-lg font-semibold">
            {money(coffee.price)}
            <span className="sr-only"> for {nw.business.bag_size}</span>
          </p>
        </div>
        <p className="mt-1 text-sm text-roast">
          {coffee.region} · {coffee.process}
        </p>
        <div className="mt-3 flex items-center gap-2 text-sm">
          <RoastMeter step={roastStep(coffee.roast)} label={coffee.roast} />
          <span className="font-medium">{coffee.roast} roast</span>
        </div>
        <p className="mb-4 mt-3 text-[15px] leading-relaxed">{capitalize(listing(coffee.notes))}.</p>
        {!compact && (
          <dl className="mt-auto space-y-1.5 border-t border-line pt-4 text-sm">
            <div className="flex gap-2">
              <dt className="w-20 shrink-0 text-roast">Best for</dt>
              <dd>{capitalize(listing(coffee.use))}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-20 shrink-0 text-roast">Size</dt>
              <dd>{nw.business.bag_size}, whole bean or ground</dd>
            </div>
          </dl>
        )}
      </div>
    </article>
  );
}

export function CafeCard({ cafe }: { cafe: Cafe }) {
  const shot = CAFE_PHOTOS[cafe.name];
  return (
    <article className="flex h-full flex-col overflow-hidden rounded-2xl border border-line bg-paper">
      {shot && (
        <div className="relative aspect-[4/3] bg-oat">
          <Photo name={shot.name} alt={shot.alt} sizes="(min-width: 1152px) 368px, (min-width: 768px) 31vw, calc(100vw - 32px)" />
        </div>
      )}
      <div className="flex flex-1 flex-col p-6">
        <h3 className="font-display text-2xl font-semibold">{cafe.name}</h3>
        <p className="mt-1 text-[15px] text-roast">{cafe.address}</p>
        <dl className="mt-5 grid grid-cols-[auto_1fr] gap-x-6 gap-y-1.5 text-sm">
          <dt className="text-roast">Mon to Fri</dt>
          <dd className="font-medium">{cafe.weekdays}</dd>
          <dt className="text-roast">Saturday</dt>
          <dd className="font-medium">{cafe.saturday}</dd>
          <dt className="text-roast">Sunday</dt>
          <dd className="font-medium">{sundayHours(cafe)}</dd>
        </dl>
        <p className="mt-5 border-t border-line pt-4 text-sm leading-relaxed">{cafe.note}</p>
      </div>
    </article>
  );
}

/** A nudge towards the chat widget, which is the product being demoed. */
export function HelpBand({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="relative overflow-hidden bg-sage">
      <BeanPattern className="text-green/15" />
      <Container className="relative flex flex-col items-start gap-6 py-12 sm:flex-row sm:items-center sm:justify-between">
        <div className="max-w-2xl">
          <h2 className="font-display text-3xl font-semibold tracking-tight">{title}</h2>
          <p className="mt-2 text-[17px] leading-relaxed text-espresso/85">{children}</p>
        </div>
        <AskButton />
      </Container>
    </section>
  );
}
