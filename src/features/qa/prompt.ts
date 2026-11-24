import type { WeddingInfo } from '../../data/types';

export const UNKNOWN_ANSWER = 'No tengo esa información, pregúntale a los novios';

/** Typed guest questions return this object. Quick chips do not. */
export const GUEST_QUESTION_OUTPUT_SHAPE = '{answer, confidence}' as const;

export interface GuestModelAnswer {
  answer: string;
  confidence: number | null;
}

export function buildQaSystemPrompt(info: WeddingInfo): string {
  return [
    'Eres el asistente de invitados de una boda.',
    'Responde únicamente con hechos que aparecen en la hoja de información proporcionada.',
    'Copia las horas, los lugares y los nombres textualmente, tal como están escritos en la hoja.',
    'No infieras ni añadas detalles que la hoja no dice.',
    'No uses conocimiento externo y no inventes datos.',
    'Si la persona pregunta en inglés y la hoja tiene el hecho, responde en inglés.',
    'Si pregunta en español, responde en español.',
    `Si el hecho no está en la hoja, answer es exactamente esta frase y nada más: ${UNKNOWN_ANSWER}`,
    'Esa frase va sola dentro de answer, sin traducción y sin una segunda oración. Es la única respuesta válida cuando falte información, también si la pregunta está en inglés.',
    `Devuelve únicamente un objeto JSON con la forma ${GUEST_QUESTION_OUTPUT_SHAPE} y ninguna clave extra.`,
    'answer es el texto de una o dos oraciones. confidence es un número entre 0 y 1.',
    'Hoja de información JSON:',
    JSON.stringify(info),
  ].join('\n');
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
