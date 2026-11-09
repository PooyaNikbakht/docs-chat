export type ProviderName = "anthropic" | "openai" | "mock";

export interface Limits {
  max_upload_mb: number;
  max_pages: number;
  document_ttl_minutes: number | null;
}

export interface Health {
  status: "ok";
  provider: ProviderName;
  model: string | null;
  public_demo: boolean;
  limits: Limits;
}

export interface DocumentInfo {
  id: string;
  name: string;
  pages: number;
  chunks: number;
  suggestions: string[];
}
