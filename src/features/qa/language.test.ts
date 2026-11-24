import { describe, expect, it } from 'vitest';
import { detectQuestionLanguage } from './language';

describe('detectQuestionLanguage', () => {
  it('reads English questions even when they name a Spanish place', () => {
    expect(detectQuestionLanguage('What time is the ceremony at Salón El Encanto?', 'es')).toBe('en');
    expect(detectQuestionLanguage('Where is Patio de ceibas?', 'es')).toBe('en');
    expect(detectQuestionLanguage('Is there parking at Salón El Encanto?', 'es')).toBe('en');
  });

  it('reads Spanish questions even when they name a place', () => {
    expect(detectQuestionLanguage('¿A qué hora es el Salón El Encanto?', 'en')).toBe('es');
    expect(detectQuestionLanguage('¿Dónde queda el Patio de ceibas?', 'en')).toBe('es');
    expect(detectQuestionLanguage('A que hora es la ceremonia en Patio de ceibas?', 'en')).toBe('es');
  });

  it('does not let a place name alone override the UI locale', () => {
    expect(detectQuestionLanguage('Salón El Encanto', 'en')).toBe('en');
    expect(detectQuestionLanguage('Patio de ceibas', 'en')).toBe('en');
    expect(detectQuestionLanguage('Salón El Encanto', 'es')).toBe('es');
    expect(detectQuestionLanguage('Patio de ceibas', 'es')).toBe('es');
  });
});
