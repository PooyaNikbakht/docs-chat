import type { Metadata } from "next";
import { CoffeeBag } from "@/components/northwind/art";
import { CoffeeCard, Container, HelpBand, PageIntro } from "@/components/northwind/ui";
import { listing, money, nw } from "@/data/northwind";

export const metadata: Metadata = { title: "Shop" };

export default function ShopPage() {
  const { shipping: ship, gift_cards: gift, coffee_notes: notes } = nw;
  return (
    <>
      <PageIntro
        eyebrow="Shop"
        title="Coffee, roasted the week you order it"
        photo={{ name: "banner-shop", alt: "Ground coffee, whole beans, two portafilters and a latte laid out on wooden boards" }}
      >
        <p>
          Every coffee comes in a {nw.business.bag_size} bag. {notes.grind} Shipping is free in Canada
          over {money(ship.free_canada_over)}.
        </p>
      </PageIntro>

      <Container className="py-14 sm:py-20">
        <p className="mb-8 rounded-xl border border-dashed border-line bg-paper px-4 py-3 text-sm text-roast">
          This is a display-only demo shop. There is no cart or checkout.
        </p>
        <h2 className="sr-only">Coffees</h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {nw.coffees.map((c) => (
            <CoffeeCard key={c.id} coffee={c} />
          ))}
        </div>

        <section aria-labelledby="gift-title" className="mt-16 grid items-center gap-8 rounded-3xl bg-sage p-8 sm:p-12 md:grid-cols-[auto_1fr]">
          <div className="mx-auto flex w-44 items-end justify-center gap-0">
            <CoffeeBag color="#5E7A5A" className="-mr-6 h-36 w-auto" />
            <CoffeeBag color="#C98B4E" className="h-28 w-auto" />
          </div>
          <div>
            <h2 id="gift-title" className="font-display text-3xl font-semibold tracking-tight">
              Gift cards
            </h2>
            <p className="mt-3 max-w-2xl text-[17px] leading-relaxed">
              Digital gift cards in {listing(gift.amounts.map(money))} amounts. {gift.delivery} {gift.expiry}{" "}
              {gift.use}
            </p>
          </div>
        </section>
      </Container>

      <HelpBand title="Not sure which coffee to pick?">
        Ask our assistant which coffee suits your brew method, or how our roast levels compare. It answers from
        our help center and shows you where it found the answer.
      </HelpBand>
    </>
  );
}
