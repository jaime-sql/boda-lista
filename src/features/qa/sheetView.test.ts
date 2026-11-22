import { describe, expect, it } from 'vitest';
import sample from '../../data/wedding_info.sample.json';
import type { WeddingInfo } from '../../data/types';
import { dateLine, partnerInitials, personName, venueLine } from './sheetView';

const info = sample as WeddingInfo;

describe('sheet view', () => {
  it('reads the couple and the venue from the wedding sheet', () => {
    expect(partnerInitials(info)).toBe('P&P');
    expect(personName(info.couple.bride)).toBe('Pareja Alfa');
    expect(venueLine(info)).toContain('Jardín El Ejemplo');
    expect(venueLine(info)).toContain('Calle Falsa 123');
    expect(venueLine(info)).not.toContain('Hacienda');
    expect(dateLine(info.date, 'es')).toContain('2026');
    expect(dateLine(info.date, 'es')).toContain('12');
  });
});
