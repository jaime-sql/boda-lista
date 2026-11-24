import type { WeddingInfo } from '../../data/types';

export type QaLang = 'es' | 'en';

export const UNKNOWN_ANSWER: string;
export const UNKNOWN_ANSWER_EN: string;
export const GUEST_QUESTION_OUTPUT_SHAPE: '{answer, confidence}';
export const GUEST_QUESTION_RESPONSE_SCHEMA: {
  type: 'object';
  properties: {
    answer: { type: 'string' };
    confidence: { type: 'number' };
  };
  required: ['answer', 'confidence'];
};

export function detectQuestionLanguage(text: string, uiLocale: QaLang): QaLang;
export function buildQaSystemPrompt(info: WeddingInfo): string;
export function buildQaUserTurn(input: { question: string; lang: QaLang; sheet: WeddingInfo }): string;
