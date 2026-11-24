import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import type { WeddingInfo } from '../../data/types';
import pack from '../../../data/wedding_info.json';
import { UNKNOWN_ANSWER } from './prompt';
import { CHIP_TOPICS, formatChipAnswer, type ChipTopic } from './chips';
import type { UiLang } from './sheetView';

const info = pack as WeddingInfo;

const PRESENT: Record<ChipTopic, { es: string[]; en: string[] }> = {
  schedule: {
    es: ['Horario:', '16:00', 'Ceremonia / Ceremony', 'Jardín Principal', '01:15'],
    en: ['Schedule:', '16:00', 'Ceremonia / Ceremony', 'Jardín Principal', '01:15'],
  },
  venue: {
    es: ['La boda es en Hacienda El Sauce', 'Km 12.5 Carretera a La Libertad', 'Ceremonia: Jardín Principal.'],
    en: ['The wedding is at Hacienda El Sauce', 'Km 12.5 Carretera a La Libertad', 'Ceremony: Jardín Principal.'],
  },
  dress: {
    es: ['Vestimenta:', 'Formal de cóctel.', 'guayabera formal'],
    en: ['Dress code:', 'Cocktail attire.', 'Guayaberas are welcome.'],
  },
  parking: {
    es: ['Parqueo:', 'Valet gratuito', '01:15'],
    en: ['Parking:', 'Do not park on the highway shoulder.', '1:15 a.m.'],
  },
  gifts: {
    es: ['Regalos:', 'Lluvia de sobres.'],
    en: ['Gifts:', 'Money envelopes are preferred.'],
  },
  contacts: {
    es: ['Contactos:', 'Elena Castro', '5550-0101', 'Roberto Solís'],
    en: ['Contacts:', 'Elena Castro', '5550-0101', 'Roberto Solís'],
  },
};

function without(topic: ChipTopic): WeddingInfo {
  const next = structuredClone(info);
  if (topic === 'schedule') next.schedule = [];
  if (topic === 'venue') {
    next.venue = { name: '', address: '', city: '', country: '' };
  }
  if (topic === 'dress') next.dress_code = { summary: '' };
  if (topic === 'parking') next.parking = { summary: '  ' };
  if (topic === 'gifts') next.gifts = { summary: '', details: '', notes: '' };
  if (topic === 'contacts') next.contacts = [];
  return next;
}

describe('quick chips', () => {
  it.each(CHIP_TOPICS)('answers %s in Spanish from the sheet', (topic) => {
    const answer = formatChipAnswer(info, topic, 'es');
    expect(answer).not.toBe(UNKNOWN_ANSWER);
    for (const fact of PRESENT[topic].es) expect(answer).toContain(fact);
  });

  it.each(CHIP_TOPICS)('answers %s in English from the sheet', (topic) => {
    const answer = formatChipAnswer(info, topic, 'en');
    expect(answer).not.toBe(UNKNOWN_ANSWER);
    for (const fact of PRESENT[topic].en) expect(answer).toContain(fact);
  });

  it.each(CHIP_TOPICS.flatMap((topic) => (['es', 'en'] as const).map((lang) => ({ topic, lang }))))(
    'refuses $topic in $lang when the field is missing',
    ({ topic, lang }: { topic: ChipTopic; lang: UiLang }) => {
      expect(formatChipAnswer(without(topic), topic, lang)).toBe(UNKNOWN_ANSWER);
    },
  );

  it('does not import the model client', () => {
    const source = readFileSync(join(process.cwd(), 'src/features/qa/chips.ts'), 'utf8');
    expect(source).not.toContain('firebase/ai');
    expect(source).not.toContain('getGenerativeModel');
    expect(source).not.toContain("from '../../ai/hybrid'");
    expect(source).not.toContain('formatClock');
  });
});
