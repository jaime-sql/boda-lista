export const FEATURES = ['guest_question', 'rsvp', 'song'] as const;

export type Feature = (typeof FEATURES)[number];
export type Route = 'device' | 'cloud' | 'sheet';
export type FallbackReason =
  | 'no_model'
  | 'low_confidence'
  | 'long_input'
  | 'no_threshold'
  | 'offline_no_threshold'
  | null;

export interface PromptLog {
  ts: string;
  feature: Feature;
  route: Route;
  fallback_reason: FallbackReason;
  latency_ms: number;
  input_chars: number;
  output_chars: number;
  model: string | null;
  confidence: number | null;
  session_id: string;
  edited_by_guest?: boolean;
}

export interface AskContext {
  feature: Feature;
  system?: string;
  confidence?: number | null;
  forceCloud?: boolean;
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
