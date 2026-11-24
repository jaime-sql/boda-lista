import { describe, expect, it } from 'vitest';
import pack from '../../../data/wedding_info.json';
import sample from '../../data/wedding_info.sample.json';
import type { WeddingInfo } from '../../data/types';
import { calendarUrl, dateLine, DEFAULT_CALENDAR_DURATION_HOURS, partnerInitials, personName, venueLine } from './sheetView';

const info = sample as WeddingInfo;
const sheet = pack as WeddingInfo;

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

  it('builds a calendar link with a real end, timezone, and Spanish details', () => {
    const url = new URL(calendarUrl(sheet, 'es'));
    const [start, end] = (url.searchParams.get('dates') ?? '').split('/');
    expect(start).toBe('20261212T160000');
    expect(end).not.toBe(start);
    expect(end).toBe(`20261212T${String(16 + DEFAULT_CALENDAR_DURATION_HOURS).padStart(2, '0')}0000`);
    expect(url.searchParams.get('ctz')).toBe('America/El_Salvador');
    expect(url.searchParams.get('details')).toBe(
      'La propiedad queda a 25 minutos en carro del centro de Santa Tecla. Hay un salón cubierto de respaldo si llueve.',
    );

    const english = new URL(calendarUrl(sheet, 'en'));
    expect(english.searchParams.get('details')).toBe(sheet.venue.notes);
  });

  it('uses an event end or duration when the sheet includes one', () => {
    const withEnd = calendarUrl({ ...info, end: '18:30' } as WeddingInfo, 'es');
    expect(new URL(withEnd).searchParams.get('dates')).toBe('20260912T160000/20260912T183000');

    const withDuration = calendarUrl({ ...info, duration_hours: 2 } as WeddingInfo, 'es');
    expect(new URL(withDuration).searchParams.get('dates')).toBe('20260912T160000/20260912T180000');

    const details = new URL(calendarUrl(info, 'es')).searchParams.get('details') ?? '';
    expect(details).toContain('Ceremonia al aire libre');
  });
});
