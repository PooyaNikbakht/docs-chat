"use client";

import Link from "next/link";
import { useState } from "react";
import type { Health } from "@/lib/types";

interface Props {
  health: Health | null;
  healthError: string | null;
  busy: "upload" | "sample" | null;
  error: string | null;
  onFile: (file: File) => void;
  onSample: () => void;
  onRetryHealth: () => void;
}

export function UploadPanel({ health, healthError, busy, error, onFile, onSample, onRetryHealth }: Props) {
  const [dragging, setDragging] = useState(false);
  const limits = health?.limits;
  const disabled = busy !== null;

  function pick(files: FileList | null) {
    const file = files?.[0];
    if (file) onFile(file);
  }

  return (
    <section aria-labelledby="start-title" className="mx-auto w-full max-w-2xl px-4 py-12 sm:px-6 sm:py-20">
      <p className="font-mono text-xs uppercase tracking-widest text-accent">Try it with your own PDF</p>
      <h1 id="start-title" className="mt-3 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
        See a support bot trained on your documents
      </h1>
      <p className="mt-4 max-w-xl text-base leading-relaxed text-muted">
        Upload a help page, FAQ, policy or price list as a PDF. In a few seconds you get a mock
        website with the chat widget answering from it, citing the page it used, and saying so
        when the document doesn&apos;t cover a question.
      </p>

      {healthError && (
        <div role="alert" className="mt-8 flex flex-wrap items-center justify-between gap-3 rounded-[8px] border border-danger px-4 py-3 text-sm text-danger">
          <span>{healthError}</span>
          <button type="button" onClick={onRetryHealth} className="font-medium underline underline-offset-4">
            Try again
          </button>
        </div>
      )}

      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!disabled) pick(e.dataTransfer.files);
        }}
        className={`mt-8 rounded-[8px] border border-dashed px-6 py-10 text-center transition-colors ${
          dragging ? "border-accent bg-accent-soft" : "border-line bg-surface"
        }`}
      >
        <p className="text-base font-medium text-ink">Drop a PDF here</p>
        <p className="mt-1 text-sm text-muted">
          {limits
            ? `Text-based PDFs up to ${limits.max_upload_mb} MB and ${limits.max_pages} pages.`
            : "Text-based PDFs only."}
        </p>
        <div className="mt-6 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
          <label
            htmlFor="pdf-input"
            className={`inline-flex min-h-11 cursor-pointer items-center justify-center rounded-[8px] bg-accent px-5 text-sm font-medium text-background focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-accent ${
              disabled ? "pointer-events-none opacity-60" : "hover:opacity-90"
            }`}
          >
            {busy === "upload" ? "Reading your PDF..." : "Choose a PDF"}
            <input
              id="pdf-input"
              type="file"
              accept="application/pdf,.pdf"
              className="sr-only"
              disabled={disabled}
              onChange={(e) => {
                pick(e.target.files);
                e.target.value = "";
              }}
            />
          </label>
          <button
            type="button"
            onClick={onSample}
            disabled={disabled}
            className="inline-flex min-h-11 items-center justify-center rounded-[8px] border border-line bg-background px-5 text-sm font-medium text-ink hover:border-accent disabled:opacity-60"
          >
            {busy === "sample" ? "Loading the sample..." : "Use the sample help center"}
          </button>
        </div>
      </div>

      <div aria-live="polite">
        {error && (
          <p role="alert" className="mt-4 rounded-[8px] border border-danger px-4 py-3 text-sm text-danger">
            {error}
          </p>
        )}
      </div>

      <p className="mt-6 text-sm leading-relaxed text-muted">
        Demo only. Don&apos;t upload sensitive documents. Files are kept in memory
        {limits?.document_ttl_minutes
          ? ` and deleted within ${limits.document_ttl_minutes === 60 ? "an hour" : `${limits.document_ttl_minutes} minutes`}.`
          : " and deleted when the server restarts."}
      </p>
      <p className="mt-3 text-sm leading-relaxed text-muted">
        Want to see it on a real-looking site first?{" "}
        <Link className="text-ink underline underline-offset-4 hover:text-accent" href="/">
          Visit the Northwind Coffee demo
        </Link>
        .
      </p>
    </section>
  );
}
