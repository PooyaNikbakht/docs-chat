import type { Metadata } from "next";
import { ContactForm } from "@/components/northwind/ContactForm";
import { CafeCard, Container, PageIntro } from "@/components/northwind/ui";
import { nw } from "@/data/northwind";

export const metadata: Metadata = { title: "Contact" };

export default function ContactPage() {
  const { business: b, wholesale } = nw;
  return (
    <>
      <PageIntro
        eyebrow="Contact"
        title="Talk to a person"
        photo={{ name: "banner-contact", alt: "A bright, quiet café with pale wooden chairs and sunlight on the floor" }}
      >
        <p>
          Our support team is around {b.support_hours}, and we reply {b.reply_time}. If your question is about an
          order, please include your order number.
        </p>
      </PageIntro>

      <Container className="grid gap-10 py-14 sm:py-20 lg:grid-cols-[1fr_1.1fr]">
        <div className="space-y-6">
          <section className="rounded-2xl border border-line bg-paper p-6">
            <h2 className="font-display text-2xl font-semibold">Customer support</h2>
            <dl className="mt-4 space-y-3 text-[15px]">
              <div>
                <dt className="text-sm text-roast">Email</dt>
                <dd className="font-medium">{b.email}</dd>
              </div>
              <div>
                <dt className="text-sm text-roast">Phone</dt>
                <dd className="font-medium">{b.phone}</dd>
              </div>
              <div>
                <dt className="text-sm text-roast">Hours</dt>
                <dd className="font-medium">{b.support_hours}</dd>
              </div>
            </dl>
          </section>
          <section className="rounded-2xl border border-line bg-paper p-6">
            <h2 className="font-display text-2xl font-semibold">Wholesale</h2>
            <p className="mt-3 text-[15px] leading-relaxed text-roast">
              We supply {wholesale.who}, with a minimum order of {wholesale.minimum}. {wholesale.contact}
            </p>
          </section>
        </div>
        <ContactForm email={b.email} />
      </Container>

      <section className="border-t border-line bg-oat/60">
        <Container className="py-14 sm:py-20">
          <h2 className="font-display text-3xl font-semibold tracking-tight">Visit a café</h2>
          <p className="mt-2 text-[15px] text-roast">{nw.cafe_notes.holidays}</p>
          <div className="mt-8 grid gap-6 md:grid-cols-3">
            {nw.cafes.map((c) => (
              <CafeCard key={c.name} cafe={c} />
            ))}
          </div>
        </Container>
      </section>
    </>
  );
}
