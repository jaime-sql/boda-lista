import type { AskResult } from '../../ai/types';
import { ask } from '../../ai/hybrid';
import { markLastPromptDetails } from '../../debug/sessionLog';
import { buildRsvpUserPrompt, RSVP_SYSTEM } from './prompt';
import { parseRsvpOutput, type RsvpExtraction } from './parse';

export interface RsvpAttempt {
  extraction: RsvpExtraction | null;
  result: AskResult;
  retried: boolean;
}

type AskRsvp = (prompt: string, system: string, forceCloud: boolean, lang: 'es' | 'en') => Promise<AskResult>;

function e2eMock(): AskResult | null {
  if (import.meta.env.VITE_E2E !== 'true') return null;
  try {
    const raw = sessionStorage.getItem('boda-lista.rsvp-mock');
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { online: AskResult; offline: AskResult };
    return navigator.onLine === false ? parsed.offline : parsed.online;
  } catch {
    return null;
  }
}

async function askRsvp(
  prompt: string,
  system: string,
  forceCloud: boolean,
  lang: 'es' | 'en',
): Promise<AskResult> {
  const mocked = e2eMock();
  if (mocked) return mocked;
  return ask(prompt, { feature: 'rsvp', system, forceCloud, lang });
}

export async function extractRsvp(
  text: string,
  lang: 'es' | 'en',
  askImpl: AskRsvp = askRsvp,
): Promise<RsvpAttempt> {
  const prompt = buildRsvpUserPrompt(text, lang);
  const first = await askImpl(prompt, RSVP_SYSTEM, false, lang);
  const parsed = parseRsvpOutput(first.text);
  if (parsed) {
    markLastPromptDetails({ confidence: parsed.confidence });
    return { extraction: parsed, result: first, retried: false };
  }
  const second = await askImpl(prompt, RSVP_SYSTEM, true, lang);
  const retried = parseRsvpOutput(second.text);
  if (retried) {
    markLastPromptDetails({ confidence: retried.confidence });
    return { extraction: retried, result: second, retried: true };
  }
  return { extraction: null, result: second, retried: true };
}
