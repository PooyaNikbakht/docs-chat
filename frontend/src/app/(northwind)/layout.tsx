import type { Metadata, Viewport } from "next";
import { Fraunces, Inter } from "next/font/google";
import { SiteFooter } from "@/components/northwind/SiteFooter";
import { SiteHeader } from "@/components/northwind/SiteHeader";
import { site } from "@/config/site";
import { nw, structuredData } from "@/data/northwind";
import "../northwind.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const fraunces = Fraunces({ variable: "--font-fraunces", subsets: ["latin"], axes: ["opsz"] });

export const metadata: Metadata = {
  title: {
    default: `${nw.business.name}: small-batch coffee from ${nw.business.city.split(",")[0]}`,
    template: `%s · ${nw.business.name}`,
  },
  description: `${nw.business.tagline} A fictional coffee roaster, built as a demo of a website support bot that answers from the business's help center.`,
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f6f0e4",
};

export default function NorthwindLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-CA" className={`${inter.variable} ${fraunces.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-espresso focus:px-4 focus:py-2 focus:text-cream"
        >
          Skip to content
        </a>
        <script
          type="application/ld+json"
          // Built from the same facts file as the site and the help center.
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData()).replace(/</g, "\\u003c") }}
        />
        <SiteHeader />
        <main id="main" className="flex-1">
          {children}
        </main>
        <SiteFooter />
        {/* The same one-line snippet a client pastes into their own site. */}
        <script src="/embed/widget.js" data-bot={site.botId} data-api={site.apiUrl} defer />
      </body>
    </html>
  );
}
