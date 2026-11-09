"use client";

import { useState } from "react";

export function CopyButton({ text, label = "Copy snippet" }: { text: string; label?: string }) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");
  return (
    <>
      <button
        type="button"
        onClick={async () => {
          try {
            await navigator.clipboard.writeText(text);
            setState("copied");
          } catch {
            setState("failed");
          }
          window.setTimeout(() => setState("idle"), 2500);
        }}
        className="inline-flex min-h-10 items-center gap-2 rounded-[8px] border border-line bg-background px-3.5 text-sm font-medium text-ink hover:border-accent"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          {state === "copied" ? (
            <path d="m5 12 5 5L20 7" />
          ) : (
            <>
              <rect x="9" y="9" width="11" height="11" rx="2" />
              <path d="M5 15V6a2 2 0 0 1 2-2h9" />
            </>
          )}
        </svg>
        {state === "copied" ? "Copied" : label}
      </button>
      <span className="sr-only" aria-live="polite">
        {state === "copied" ? "Snippet copied to the clipboard." : state === "failed" ? "Copy failed. Select the snippet and copy it by hand." : ""}
      </span>
    </>
  );
}
