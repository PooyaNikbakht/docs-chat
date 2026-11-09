import type { Metadata } from "next";
import { TryClient } from "@/components/demo/TryClient";

export const metadata: Metadata = {
  title: "Try it with your PDF",
  description: "Upload a PDF and try a website support bot that answers from it, with page citations.",
};

export default function TryPage() {
  return <TryClient />;
}
