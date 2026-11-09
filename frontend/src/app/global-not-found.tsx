import Link from "next/link";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./demo.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Page not found",
  robots: { index: false, follow: false },
};

// The app has two root layouts (the sample site and the demo pages), so unmatched URLs
// get this standalone page.
export default function GlobalNotFound() {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="flex min-h-full items-center justify-center px-4">
        <main className="max-w-md text-center">
          <p className="font-mono text-xs uppercase tracking-widest text-accent">404</p>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-ink">We couldn&apos;t find that page</h1>
          <p className="mt-3 text-muted">
            Try the{" "}
            <Link className="text-ink underline underline-offset-4" href="/">
              sample site
            </Link>
            ,{" "}
            <a className="text-ink underline underline-offset-4" href="/try">
              your own PDF
            </a>{" "}
            or the{" "}
            <a className="text-ink underline underline-offset-4" href="/install">
              install guide
            </a>
            .
          </p>
        </main>
      </body>
    </html>
  );
}
