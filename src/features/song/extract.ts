import type { AskResult } from '../../ai/types';
import { ask } from '../../ai/hybrid';
import { markLastPromptDetails } from '../../debug/sessionLog';
import { buildSongUserPrompt, SONG_SYSTEM } from './prompt';
import { parseSongOutput, type SongExtraction } from './parse';

export interface SongAttempt {
  extraction: SongExtraction | null;
  result: AskResult;
  retried: boolean;
}

type AskSong = (prompt: string, system: string, forceCloud: boolean, lang: 'es' | 'en') => Promise<AskResult>;

type SongE2EMock = {
  online: AskResult;
  offline: AskResult;
  byText?: Record<string, { online?: AskResult; offline?: AskResult }>;
};

function e2eMock(rawText: string): AskResult | null {
  if (import.meta.env.VITE_E2E !== 'true') return null;
  try {
    const raw = sessionStorage.getItem('boda-lista.song-mock');
    if (!raw) return null;
    const parsed = JSON.parse(raw) as SongE2EMock;
    const isOffline = navigator.onLine === false;
    const exact = parsed.byText?.[rawText];
    if (exact) {
      const picked = isOffline ? exact.offline : exact.online;
      if (picked) return picked;
    }
    return isOffline ? parsed.offline : parsed.online;
  } catch {
    return null;
  }
}

async function askSong(
  prompt: string,
  system: string,
  forceCloud: boolean,
  lang: 'es' | 'en',
  rawText: string,
): Promise<AskResult> {
  const mocked = e2eMock(rawText);
  if (mocked) return mocked;
  return ask(prompt, { feature: 'song', system, forceCloud, lang });
}

/** Extracts normalized song title, artist, energy, and ambiguity via hybrid inference. */
export async function extractSong(
  text: string,
  lang: 'es' | 'en',
  askImpl?: AskSong,
): Promise<SongAttempt> {
  const cleanText = text.trim();
  const prompt = buildSongUserPrompt(cleanText, lang);
  const call: AskSong = askImpl ?? ((p, s, force, l) => askSong(p, s, force, l, cleanText));
  const first = await call(prompt, SONG_SYSTEM, false, lang);
  const parsed = parseSongOutput(first.text);
  if (parsed) {
    markLastPromptDetails({ confidence: parsed.confidence });
    return { extraction: parsed, result: first, retried: false };
  }
  const second = await call(prompt, SONG_SYSTEM, true, lang);
  const retried = parseSongOutput(second.text);
  if (retried) {
    markLastPromptDetails({ confidence: retried.confidence });
    return { extraction: retried, result: second, retried: true };
  }
  return { extraction: null, result: second, retried: true };
}
