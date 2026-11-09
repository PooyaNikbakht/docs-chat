import Link from "next/link";
import { site } from "@/config/site";
import { nw } from "@/data/northwind";
import { NAV } from "./nav";
import { LogoMark } from "./art";

export function SiteFooter() {
  const b = nw.business;
  return (
    <footer className="mt-auto bg-espresso text-cream">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-14 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr_1.2fr]">
        <div>
          <div className="flex items-center gap-2.5">
            <LogoMark size={30} light />
            <span className="font-display text-xl font-semibold">{b.name}</span>
          </div>
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-cream/75">{b.tagline} Roasting in {b.city} since {b.founded}.</p>
        </div>
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-[0.16em] text-cream/60">Explore</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {NAV.map((item) => (
              <li key={item.href}>
                <Link className="text-cream/90 underline-offset-4 hover:underline" href={item.href}>
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-[0.16em] text-cream/60">Cafés</h2>
          <ul className="mt-4 space-y-2 text-sm text-cream/90">
            {nw.cafes.map((c) => (
              <li key={c.name}>{c.name}</li>
            ))}
          </ul>
        </div>
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-[0.16em] text-cream/60">Get in touch</h2>
          <ul className="mt-4 space-y-2 text-sm text-cream/90">
            <li>{b.email}</li>
            <li>{b.phone}</li>
            <li className="text-cream/70">{b.support_hours}</li>
          </ul>
        </div>
      </div>
      <div className="border-t border-cream/15">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-5 text-xs text-cream/70 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p>
            <a className="text-cream underline-offset-4 hover:underline" href={site.creditUrl}>
              Fictional business. Demo by {site.author}
            </a>
          </p>
          {/* Plain links for the demo pages: they use a different root layout. */}
          <p className="flex flex-wrap gap-x-4 gap-y-1">
            <a className="underline-offset-4 hover:text-cream hover:underline" href="/try">
              Try it with your PDF
            </a>
            <a className="underline-offset-4 hover:text-cream hover:underline" href="/booking">
              Booking demo
            </a>
            <a className="underline-offset-4 hover:text-cream hover:underline" href="/install">
              How to install
            </a>
            <Link className="underline-offset-4 hover:text-cream hover:underline" href="/credits">
              Photo credits
            </Link>
          </p>
        </div>
      </div>
    </footer>
  );
}
