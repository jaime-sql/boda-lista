import { describe, expect, it } from 'vitest';
import sample from '../../data/wedding_info.sample.json';
import type { WeddingInfo } from '../../data/types';
import { UNKNOWN_ANSWER, UNKNOWN_ANSWER_EN, buildQaSystemPrompt, buildQaUserTurn, parseGuestModelAnswer } from './prompt';

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

  it('answers in the declared lang and refuses in that language', () => {
    expect(UNKNOWN_ANSWER_EN).toBe("I don't have that information, ask the couple");
    const prompt = buildQaSystemPrompt(sample as WeddingInfo);
    expect(prompt).toContain('No infieras el idioma. Responde siempre en el idioma declarado en el turno del usuario.');
    expect(prompt).toContain('Si lang es en, answer va en inglés. Si lang es es, answer va en español.');
    expect(prompt).toContain(UNKNOWN_ANSWER);
    expect(prompt).toContain(UNKNOWN_ANSWER_EN);
  });

  it('puts lang and the answer-language line on the user turn', () => {
    const sheet = sample as WeddingInfo;
    const english = buildQaUserTurn({
      question: 'What time is Salón El Encanto?',
      lang: 'en',
      sheet,
    });
    expect(english).toContain('lang: en');
    expect(english).toContain('Answer language: English');
    expect(english).toContain('What time is Salón El Encanto?');
    expect(english).toContain('Jardín El Ejemplo');

    const spanish = buildQaUserTurn({
      question: '¿A qué hora es Patio de ceibas?',
      lang: 'es',
      sheet,
    });
    expect(spanish).toContain('lang: es');
    expect(spanish).toContain('Idioma de respuesta: español');
    expect(spanish).toContain('¿A qué hora es Patio de ceibas?');
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
