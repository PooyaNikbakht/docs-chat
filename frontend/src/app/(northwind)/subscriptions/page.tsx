import type { Metadata } from "next";
import { Cup } from "@/components/northwind/art";
import { Container, Eyebrow, HelpBand, PageIntro } from "@/components/northwind/ui";
import { nw } from "@/data/northwind";

export const metadata: Metadata = { title: "Subscriptions" };

export default function SubscriptionsPage() {
  const sub = nw.subscriptions;
  const steps = [
    ["Pick your coffee", `Choose any coffee, or ${sub.roasters_choice.split(" sends")[0]} for a different single origin each time.`],
    ["Choose a rhythm", `Deliveries ${sub.frequencies}, whole bean or ground for your brewer.`],
    ["Change it whenever", `Pause for up to ${sub.pause_max}, skip a delivery, or cancel. No fees.`],
  ];
  return (
    <>
      <PageIntro
        eyebrow="Subscriptions"
        title={`Fresh coffee ${sub.frequencies}`}
        photo={{ name: "banner-subscriptions", alt: "Two hands holding open a fresh bag of roasted coffee beans" }}
      >
        <p>
          Subscribers save {sub.discount_percent}% on every bag. {sub.free_shipping}
        </p>
      </PageIntro>

      <Container className="py-14 sm:py-20">
        <h2 className="font-display text-3xl font-semibold tracking-tight">How it works</h2>
        <ol className="mt-8 grid gap-6 md:grid-cols-3">
          {steps.map(([title, body], i) => (
            <li key={title} className="rounded-2xl border border-line bg-paper p-6">
              <span className="font-display text-4xl font-semibold text-crema" aria-hidden="true">
                {i + 1}
              </span>
              <h3 className="mt-3 font-display text-xl font-semibold">{title}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-roast">{body}</p>
            </li>
          ))}
        </ol>
      </Container>

      <section className="border-y border-line bg-paper">
        <Container className="grid items-center gap-12 py-14 sm:py-20 lg:grid-cols-[1fr_0.7fr]">
          <div>
            <Eyebrow>The fine print, in plain words</Eyebrow>
            <h2 className="mt-3 font-display text-3xl font-semibold tracking-tight">Managing your subscription</h2>
            <dl className="mt-8 divide-y divide-line border-y border-line">
              {[
                ["Pause", `Pause for up to ${sub.pause_max} at a time. It restarts on the date you pick.`],
                ["Skip", sub.skip],
                ["Cancel", sub.cancel],
                ["Deadline", `Changes apply to your next delivery when you make them at least ${sub.change_deadline}.`],
                ["Where", sub.manage],
              ].map(([term, detail]) => (
                <div key={term} className="grid gap-1 py-4 sm:grid-cols-[120px_1fr] sm:gap-6">
                  <dt className="font-semibold">{term}</dt>
                  <dd className="text-[15px] leading-relaxed text-roast">{detail}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="rounded-3xl bg-sage p-10">
            <Cup className="h-auto w-full" />
          </div>
        </Container>
      </section>

      <HelpBand title="Want to pause or skip?">
        Ask our assistant how pausing, skipping and the change deadline work. It quotes the exact part of our
        help center it used.
      </HelpBand>
    </>
  );
}
