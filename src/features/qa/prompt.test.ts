import { describe, expect, it } from 'vitest';
import sample from '../../data/wedding_info.sample.json';
import type { WeddingInfo } from '../../data/types';
import { UNKNOWN_ANSWER, buildQaSystemPrompt } from './prompt';

describe('guest prompt', () => {
  it('uses the exact out-of-scope sentence and the sample sheet', () => {
    expect(UNKNOWN_ANSWER).toBe('No tengo esa información, pregúntale a los novios');
    const prompt = buildQaSystemPrompt(sample as WeddingInfo);
    expect(prompt).toContain(UNKNOWN_ANSWER);
    expect(prompt).toContain('Jardín El Ejemplo');
    expect(prompt).toContain('Calle Falsa 123');
    expect(prompt).not.toContain('force');
  });
});
