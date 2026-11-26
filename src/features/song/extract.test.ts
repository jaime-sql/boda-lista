import { describe, expect, it, vi } from 'vitest';
import type { AskResult } from '../../ai/types';
import { extractSong } from './extract';

const valid = {
  title: 'Perfect',
  artist: 'Ed Sheeran',
  energy: 'slow',
  ambiguous: false,
  confidence: 0.88,
};

function result(text: string, route: AskResult['route']): AskResult {
  return {
    text,
    route,
    fallbackReason: route === 'cloud' ? 'no_threshold' : 'offline_no_threshold',
    latencyMs: 8,
    inputChars: 42,
    outputChars: text.length,
    model: route === 'cloud' ? 'gemini-3.5-flash-lite' : 'gemini-nano',
  };
}

describe('extractSong', () => {
  it('returns the parsed song on the first call when JSON is valid', async () => {
    const askImpl = vi.fn<(prompt: string, system: string, forceCloud: boolean, lang: 'es' | 'en') => Promise<AskResult>>(
      async () => result(JSON.stringify(valid), 'device'),
    );
    const attempt = await extractSong('  Para el vals pedimos Perfect de Ed Sheeran ', 'es', askImpl);
    expect(askImpl).toHaveBeenCalledOnce();
    expect(askImpl.mock.calls[0]?.[2]).toBe(false);
    expect(attempt.retried).toBe(false);
    expect(attempt.extraction).toEqual(valid);
  });

  it('retries once forcing cloud when the first output fails schema validation', async () => {
    const askImpl = vi
      .fn<(prompt: string, system: string, forceCloud: boolean, lang: 'es' | 'en') => Promise<AskResult>>()
      .mockResolvedValueOnce(result('not json', 'device'))
      .mockResolvedValueOnce(result(JSON.stringify(valid), 'cloud'));
    const attempt = await extractSong('Perfect by Ed Sheeran', 'en', askImpl);
    expect(askImpl).toHaveBeenCalledTimes(2);
    expect(askImpl.mock.calls[1]?.[2]).toBe(true);
    expect(attempt.retried).toBe(true);
    expect(attempt.extraction).toEqual(valid);
    expect(attempt.result.route).toBe('cloud');
  });

  it('returns null extraction if both attempts produce invalid JSON', async () => {
    const askImpl = vi
      .fn<(prompt: string, system: string, forceCloud: boolean, lang: 'es' | 'en') => Promise<AskResult>>()
      .mockResolvedValueOnce(result('bad 1', 'cloud'))
      .mockResolvedValueOnce(result(JSON.stringify({ ...valid, ambiguous: true }), 'cloud'));
    const attempt = await extractSong('algo alegre', 'es', askImpl);
    expect(askImpl).toHaveBeenCalledTimes(2);
    expect(attempt.retried).toBe(true);
    expect(attempt.extraction).toBeNull();
  });
});
