import Link from "next/link";
import { site } from "@/config/site";
import { NavLinks } from "./NavLinks";

export function DemoHeader() {
  return (
    <header className="border-b border-line">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5 rounded-md">
          <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">
            <rect width="28" height="28" rx="8" fill="var(--accent)" />
            <path d="M8 10.5h12M8 14.5h8" stroke="var(--background)" strokeWidth="2.2" strokeLinecap="round" />
            <circle cx="20" cy="19" r="2.4" fill="var(--background)" />
          </svg>
          <span className="text-[15px] font-semibold tracking-tight text-ink">{site.productName}</span>
        </Link>
        <NavLinks />
      </div>
    </header>
  );
}

export function DemoFooter() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2 px-4 py-6 text-sm text-muted sm:px-6">
        <p>
          Built by{" "}
          <a className="text-ink underline underline-offset-4 hover:text-accent" href={site.githubUrl}>
            {site.author}
          </a>
        </p>
        <div className="flex gap-5">
          <a className="underline underline-offset-4 hover:text-accent" href={site.portfolioUrl}>
            Pooya&apos;s site
          </a>
          {site.repoUrl ? (
            <a className="underline underline-offset-4 hover:text-accent" href={site.repoUrl}>
              Source on GitHub
            </a>
          ) : null}
        </div>
      </div>
    </footer>
  );
}
