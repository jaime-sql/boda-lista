import { rememberPromptLog } from '../debug/sessionLog';
import { missingEnv } from '../firebase/config';
import { writePromptLog } from '../firebase/logs';
import { getSessionId } from '../lib/session';
import type { PromptLog } from './types';

export const SHEET_ROUTE = 'sheet' as const;

export function sheetPromptLog(
  outputChars: number,
  lang: 'es' | 'en',
  sessionId = getSessionId(),
): PromptLog {
  return {
    ts: new Date().toISOString(),
    feature: 'guest_question',
    route: SHEET_ROUTE,
    fallback_reason: null,
    latency_ms: 0,
    input_chars: 0,
    output_chars: Math.max(0, Math.round(outputChars)),
    model: null,
    confidence: null,
    lang,
    session_id: sessionId,
  };
}

/** Records a chip answer. Nothing is sent to a model. */
export async function logSheetDecision(outputChars: number, lang: 'es' | 'en'): Promise<void> {
  const entry = sheetPromptLog(outputChars, lang);
  if (missingEnv().length > 0) {
    rememberPromptLog('sheet-local', entry);
    return;
  }
  try {
    const id = await writePromptLog(entry);
    rememberPromptLog(id, entry);
  } catch {
    rememberPromptLog('sheet-local', entry);
  }
}
