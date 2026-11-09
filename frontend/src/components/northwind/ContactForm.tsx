"use client";

import { useState } from "react";

const field =
  "mt-1.5 block w-full rounded-xl border border-line bg-paper px-4 py-3 text-base text-espresso placeholder:text-roast/60 focus:border-green focus:outline-none focus:ring-2 focus:ring-green/30";

/** A display-only form: this is a demo site, so nothing is sent. */
export function ContactForm({ email }: { email: string }) {
  const [sent, setSent] = useState(false);
  return (
    <form
      className="rounded-2xl border border-line bg-paper p-6 sm:p-8"
      onSubmit={(e) => {
        e.preventDefault();
        setSent(true);
      }}
    >
      <h2 className="font-display text-2xl font-semibold">Send us a message</h2>
      <div className="mt-6 grid gap-5 sm:grid-cols-2">
        <label className="block text-sm font-medium">
          Name
          <input name="name" autoComplete="name" required className={field} />
        </label>
        <label className="block text-sm font-medium">
          Email
          <input name="email" type="email" autoComplete="email" required className={field} />
        </label>
        <label className="block text-sm font-medium sm:col-span-2">
          Order number <span className="font-normal text-roast">(optional)</span>
          <input name="order" className={field} />
        </label>
        <label className="block text-sm font-medium sm:col-span-2">
          Message
          <textarea name="message" rows={5} required className={field} />
        </label>
      </div>
      <button
        type="submit"
        className="mt-6 inline-flex min-h-12 items-center rounded-full bg-espresso px-6 text-[15px] font-semibold text-cream hover:bg-roast"
      >
        Send message
      </button>
      <p aria-live="polite" className="mt-4 text-sm text-roast">
        {sent
          ? `Thanks! This is a demo site, so nothing was sent. In real life this would reach ${email}.`
          : "Demo: nothing is sent."}
      </p>
    </form>
  );
}
