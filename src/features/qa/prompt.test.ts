import { describe, expect, it } from 'vitest';
import sample from '../../data/wedding_info.sample.json';
import type { WeddingInfo } from '../../data/types';
import { UNKNOWN_ANSWER, buildQaSystemPrompt, parseGuestModelAnswer } from './prompt';

describe('guest prompt', () => {
  it('uses the exact out-of-scope sentence and the sample sheet', () => {
    expect(UNKNOWN_ANSWER).toBe('No tengo esa información, pregúntale a los novios');
    const prompt = buildQaSystemPrompt(sample as WeddingInfo);
    expect(prompt).toContain(UNKNOWN_ANSWER);
    expect(prompt).toContain('{answer, confidence}');
    expect(prompt).toContain('textualmente');
    expect(prompt).toContain('No infieras');
    expect(prompt).toContain('una o dos oraciones');
    expect(prompt).toContain('Jardín El Ejemplo');
    expect(prompt).toContain('Calle Falsa 123');
    expect(prompt).not.toContain('force');
  });

  it('reads the answer object and leaves plain text alone', () => {
    expect(parseGuestModelAnswer(`{"answer":"${UNKNOWN_ANSWER}","confidence":0.2}`)).toEqual({
      answer: UNKNOWN_ANSWER,
      confidence: 0.2,
    });
    expect(parseGuestModelAnswer('La ceremonia es a las 16:00.')).toEqual({
      answer: 'La ceremonia es a las 16:00.',
      confidence: null,
    });
  });
});
