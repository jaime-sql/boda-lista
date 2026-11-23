import { describe, expect, it, vi } from 'vitest';
import type { AskResult } from '../../ai/types';
import { extractRsvp } from './extract';

const valid = {
  attending: 'yes',
  party_size: 3,
  meal_restrictions: ['vegetarian'],
  kids_count: 0,
  needs_ride: null,
  ambiguous: false,
  confidence: 0.7,
};

function result(text: string, route: AskResult['route']): AskResult {
  return {
    text,
    route,
    fallbackReason: route === 'cloud' ? 'no_threshold' : 'offline_no_threshold',
    latencyMs: 5,
    inputChars: 30,
    outputChars: text.length,
    model: route === 'cloud' ? 'gemini-3.5-flash-lite' : 'gemini-nano',
  };
}

describe('extractRsvp', () => {
  it('asks once when the JSON matches the rsvp schema', async () => {
    const askImpl = vi.fn<(prompt: string, system: string, forceCloud: boolean) => Promise<AskResult>>(
      async () => result(JSON.stringify(valid), 'cloud'),
    );
    const attempt = await extractRsvp('Vamos tres', 'es', askImpl);
    expect(askImpl).toHaveBeenCalledOnce();
    expect(askImpl.mock.calls[0]?.[2]).toBe(false);
    expect(attempt.extraction?.party_size).toBe(3);
    expect(attempt.retried).toBe(false);
  });

  it('retries once in cloud and then gives up', async () => {
    const askImpl = vi
      .fn<(prompt: string, system: string, forceCloud: boolean) => Promise<AskResult>>()
      .mockResolvedValueOnce(result('not json', 'cloud'))
      .mockResolvedValueOnce(result('still not', 'cloud'));
    const attempt = await extractRsvp('Vamos', 'en', askImpl);
    expect(askImpl).toHaveBeenCalledTimes(2);
    expect(askImpl.mock.calls[1]?.[2]).toBe(true);
    expect(attempt.extraction).toBeNull();
    expect(attempt.retried).toBe(true);
  });
});
