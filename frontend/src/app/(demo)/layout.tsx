import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { DemoFooter, DemoHeader } from "@/components/demo/chrome";
import "../demo.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const mono = JetBrains_Mono({ variable: "--font-jetbrains-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: "Website support bot", template: "%s · Website support bot" },
  description:
    "A chat widget for your website that answers visitors from your own documents, cites the page it used, and hands off to a human when it doesn't know.",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0b0f14" },
  ],
};

export default function DemoLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <DemoHeader />
        <main id="main" className="flex flex-1 flex-col">
          {children}
        </main>
        <DemoFooter />
      </body>
    </html>
  );
}
