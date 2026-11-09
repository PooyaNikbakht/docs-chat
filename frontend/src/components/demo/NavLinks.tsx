"use client";

import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Sample site" },
  { href: "/try", label: "Try your PDF" },
  { href: "/booking", label: "Booking" },
  { href: "/install", label: "Install" },
];

// Plain <a> links: the sample site uses a different root layout, so it is a full page load anyway.
export function NavLinks() {
  const pathname = usePathname();
  return (
    <nav aria-label="Demo">
      <ul className="flex items-center gap-1 text-sm">
        {LINKS.map((l) => (
          <li key={l.href}>
            <a
              href={l.href}
              aria-current={pathname === l.href ? "page" : undefined}
              className="rounded-md px-2.5 py-2 text-muted hover:text-ink aria-[current=page]:font-medium aria-[current=page]:text-ink"
            >
              {l.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
