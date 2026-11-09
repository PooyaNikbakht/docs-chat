"use client";

import { useEffect, useState } from "react";
import { site } from "@/config/site";
import { loadWidget } from "@/lib/widget";

const SERVICES = [
  ["Classic haircut", "$38", "30 min"],
  ["Skin fade", "$45", "45 min"],
  ["Haircut and beard", "$62", "60 min"],
  ["Beard trim and line-up", "$25", "20 min"],
  ["Hot towel shave", "$42", "40 min"],
  ["Kids cut", "$28", "25 min"],
] as const;

const HOURS = [
  ["Mon", "9 AM to 5 PM"],
  ["Tue", "9 AM to 7 PM"],
  ["Wed, Thu", "9 AM to 8 PM"],
  ["Fri", "10 AM to 8 PM"],
  ["Sat", "9 AM to 7 PM"],
  ["Sun", "10 AM to 4 PM"],
] as const;

/** A stand-in barbershop site with the booking receptionist in the corner. */
export function BookingDemo() {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let widget: DocsChatWidget | null = null;
    let cancelled = false;
    loadWidget()
      .then((api) => {
        if (cancelled) return;
        widget = api.mount({ api: site.apiUrl, bot: "kingsway", open: window.innerWidth >= 768 });
      })
      .catch((err: Error) => setError(err.message));
    return () => {
      cancelled = true;
      widget?.destroy();
    };
  }, []);

  return (
    <div className="flex flex-1 flex-col">
      <div className="border-b border-line bg-accent-soft">
        <div className="mx-auto max-w-5xl px-4 py-4 sm:px-6">
          <p className="max-w-3xl text-sm leading-relaxed text-ink lg:max-w-xl">
            <span className="font-semibold">Booking receptionist demo.</span> Ask the chat for a time, tap one,
            give a name and email, and confirm. Open times come only from the business&apos;s booking system
            through a tool call, and nothing is booked until you press Book it. This demo runs on a sample weekly
            schedule, so no real appointment is made.
          </p>
          {error && (
            <p role="alert" className="mt-2 text-sm text-danger">
              {error}
            </p>
          )}
        </div>
      </div>

      <div className="mx-auto w-full max-w-5xl flex-1 px-4 py-10 sm:px-6">
        <div className="flex items-center justify-between border-b border-line pb-5">
          <span className="text-base font-semibold tracking-tight text-ink">Kingsway Cuts</span>
          <span className="text-sm text-muted">Bloor West, Toronto</span>
        </div>

        <div className="py-12 md:max-w-xl">
          <p className="font-mono text-xs uppercase tracking-wider text-muted">Fictional barbershop</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            Book a chair any time, even at midnight
          </h1>
          <p className="mt-4 text-base leading-relaxed text-muted">
            The chat checks which times are open, offers them as buttons, and books the one you pick after you
            confirm. Questions about the shop get answers from its help center, with the source.
          </p>
          <button
            type="button"
            onClick={() => window.DocsChat?.open()}
            className="mt-6 inline-flex min-h-11 items-center justify-center rounded-[8px] bg-ink px-5 text-sm font-medium text-background hover:bg-ink/90"
          >
            Book an appointment
          </button>
        </div>

        <div className="grid gap-6 md:grid-cols-[1.4fr_1fr]">
          <section aria-labelledby="services" className="rounded-[8px] border border-line p-5">
            <h2 id="services" className="text-base font-semibold text-ink">
              Services
            </h2>
            <ul className="mt-3 divide-y divide-line">
              {SERVICES.map(([name, price, length]) => (
                <li key={name} className="flex items-baseline justify-between gap-4 py-2.5 text-sm">
                  <span className="text-ink">{name}</span>
                  <span className="shrink-0 text-muted">
                    {price} <span aria-hidden="true">·</span> {length}
                  </span>
                </li>
              ))}
            </ul>
          </section>
          <section aria-labelledby="hours" className="rounded-[8px] border border-line p-5">
            <h2 id="hours" className="text-base font-semibold text-ink">
              Hours
            </h2>
            <dl className="mt-3 divide-y divide-line text-sm">
              {HOURS.map(([day, time]) => (
                <div key={day} className="flex justify-between gap-4 py-2.5">
                  <dt className="text-muted">{day}</dt>
                  <dd className="text-ink">{time}</dd>
                </div>
              ))}
            </dl>
          </section>
        </div>
      </div>
    </div>
  );
}
