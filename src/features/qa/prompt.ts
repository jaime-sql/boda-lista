export {
  UNKNOWN_ANSWER,
  UNKNOWN_ANSWER_EN,
  GUEST_QUESTION_OUTPUT_SHAPE,
  buildQaSystemPrompt,
  buildQaUserTurn,
} from './qaRequest.js';
export type { QaLang } from './qaRequest.js';

export interface GuestModelAnswer {
  answer: string;
  confidence: number | null;
}

function readConfidence(value: unknown): number | null {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 1) return null;
  return value;
}

function readAnswerObject(text: string): GuestModelAnswer | null {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)\s*```/i);
  const candidate = fenced?.[1] ?? text;
  const start = candidate.indexOf('{');
  const end = candidate.lastIndexOf('}');
  if (start < 0 || end <= start) return null;
  try {
    const value: unknown = JSON.parse(candidate.slice(start, end + 1));
    if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
    const row = value as { answer?: unknown; confidence?: unknown };
    if (typeof row.answer !== 'string') return null;
    return { answer: row.answer.trim(), confidence: readConfidence(row.confidence) };
  } catch {
    return null;
  }
}

export function parseGuestModelAnswer(text: string): GuestModelAnswer {
  const trimmed = text.trim();
  return readAnswerObject(trimmed) ?? { answer: trimmed, confidence: null };
}
