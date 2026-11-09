"use client";

import { useCallback, useEffect, useState } from "react";
import { site } from "@/config/site";
import { ApiError, getHealth, loadSample, uploadDocument } from "@/lib/api";
import type { DocumentInfo, Health } from "@/lib/types";
import { loadWidget } from "@/lib/widget";
import { MockSite } from "./MockSite";
import { UploadPanel } from "./UploadPanel";

function message(err: unknown): string {
  return err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
}

export function TryClient() {
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"upload" | "sample" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [doc, setDoc] = useState<DocumentInfo | null>(null);

  const checkHealth = useCallback(async () => {
    setHealthError(null);
    try {
      setHealth(await getHealth());
    } catch (err) {
      setHealthError(message(err));
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void checkHealth();
  }, [checkHealth]);

  // Mount the widget on the uploaded document, and remove it when the document changes.
  useEffect(() => {
    if (!doc) return;
    let widget: DocsChatWidget | null = null;
    let cancelled = false;
    loadWidget()
      .then((api) => {
        if (cancelled) return;
        widget = api.mount({
          api: site.apiUrl,
          document: doc.id,
          open: true,
          overrides: { name: "Support", accent_color: "#0F766E", handoff_url: "#contact", tooltip: null },
        });
      })
      .catch((err: Error) => setError(err.message));
    return () => {
      cancelled = true;
      widget?.destroy();
    };
  }, [doc]);

  async function run(kind: "upload" | "sample", action: () => Promise<DocumentInfo>) {
    setBusy(kind);
    setError(null);
    try {
      const info = await action();
      setDoc(info);
      window.scrollTo({ top: 0 });
    } catch (err) {
      setError(message(err));
    } finally {
      setBusy(null);
    }
  }

  if (doc) {
    return <MockSite doc={doc} onReset={() => setDoc(null)} />;
  }
  return (
    <UploadPanel
      health={health}
      healthError={healthError}
      busy={busy}
      error={error}
      onFile={(file) => run("upload", () => uploadDocument(file))}
      onSample={() => run("sample", loadSample)}
      onRetryHealth={checkHealth}
    />
  );
}
