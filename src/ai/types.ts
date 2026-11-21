export const FEATURES = ['qa', 'rsvp', 'songs', 'budget', 'seating'] as const;

export type Feature = (typeof FEATURES)[number];
export type Route = 'device' | 'cloud';
export type FallbackReason = 'no_model' | 'low_confidence' | 'long_input' | null;

export interface PromptLog {
  ts: string;
  feature: Feature;
  route: Route;
  fallback_reason: FallbackReason;
  latency_ms: number;
  input_chars: number;
  output_chars: number;
  model: string;
  confidence: number | null;
  session_id: string;
}

export interface AskContext {
  feature: Feature;
  system?: string;
  confidence?: number | null;
}

export interface AskResult {
  text: string;
  route: Route;
  fallbackReason: FallbackReason;
  latencyMs: number;
  inputChars: number;
  outputChars: number;
  model: string;
}
