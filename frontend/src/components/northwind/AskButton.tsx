"use client";

// Opens the chat widget that the page loads through the embed snippet.
export function AskButton({ label = "Ask our assistant" }: { label?: string }) {
  return (
    <button
      type="button"
      onClick={() => window.DocsChat?.open()}
      className="inline-flex min-h-12 shrink-0 items-center gap-2 rounded-full bg-green px-6 text-[15px] font-semibold text-cream transition-colors hover:bg-espresso"
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.8A8 8 0 1 1 21 12Z" />
      </svg>
      {label}
    </button>
  );
}
