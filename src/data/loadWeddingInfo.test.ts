import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import sample from './wedding_info.sample.json';
import {
  PACK_SHEET_PATH,
  activeSheetOrigin,
  isWeddingInfo,
  loadBundledWeddingInfo,
  loadFromLoaders,
  resolveWeddingInfo,
} from './loadWeddingInfo';
import type { WeddingInfo } from './types';

const sheet = sample as WeddingInfo;

function memoryStorage(seed?: string): Storage {
  const map = new Map<string, string>();
  if (seed) map.set('boda-lista.wedding-info', seed);
  return {
    get length() {
      return map.size;
    },
    clear: () => map.clear(),
    getItem: (key) => map.get(key) ?? null,
    setItem: (key, value) => {
      map.set(key, String(value));
    },
    removeItem: (key) => {
      map.delete(key);
    },
    key: (index) => [...map.keys()][index] ?? null,
  };
}

describe('wedding info loader', () => {
  it('prefers the data pack and falls back to the sample', async () => {
    expect(PACK_SHEET_PATH).toBe('data/wedding_info.json');
    expect(activeSheetOrigin({})).toBe('sample');
    const source = readFileSync(join(process.cwd(), 'src/data/loadWeddingInfo.ts'), 'utf8');
    expect(source).toContain("import.meta.glob");
    expect(source).toContain('../../data/wedding_info.json');
    expect(source).not.toContain("from '../../data/wedding_info.json'");

    const pack = {
      ...sheet,
      venue: { ...sheet.venue, name: 'Pack Hall' },
    };
    await expect(loadFromLoaders({}, sheet)).resolves.toBe(sheet);
    await expect(
      loadFromLoaders({ 'data/wedding_info.json': async () => ({ default: pack }) }, sheet),
    ).resolves.toMatchObject({ venue: { name: 'Pack Hall' } });
    await expect(
      loadFromLoaders(
        { 'data/wedding_info.json': async () => ({ default: { synthetic: false } }) },
        sheet,
      ),
    ).resolves.toBe(sheet);
    expect(isWeddingInfo(sheet)).toBe(true);
  });

  it('returns the data-pack sheet when data/wedding_info.json is present', async () => {
    expect(activeSheetOrigin()).toBe('pack');
    const loaded = await loadBundledWeddingInfo();
    expect(loaded.venue.name).toBe('Hacienda El Sauce');
    expect(loaded.couple.bride).toEqual({ first_name: 'Lucía', last_name: 'Mendoza' });
    expect(loaded.couple.groom).toEqual({ first_name: 'Andrés', last_name: 'Solís' });
    expect(loaded.date).toBe('2026-12-12');
    expect(loaded.venue.name).not.toBe(sheet.venue.name);
    expect(loaded.synthetic).toBe(true);
    expect(loaded.venue.notes).toContain('25-minute drive from central Santa Tecla');
    expect(loaded.venue.notes).toContain('covered backup hall');
    expect(loaded.venue.notes_es).toContain('25 minutos');
    expect(loaded.venue.notes_es).toContain('Santa Tecla');
    expect(loaded.venue.notes_es).toContain('salón cubierto');
    expect(loaded.parking.details).toContain('estacionamiento norte');
    expect(loaded.parking.details).toContain('15:00');
    expect(loaded.parking.details).toContain('01:15');
    expect(loaded.parking.details_en).toContain('estacionamiento norte');
    expect(loaded.parking.details_en).toContain('Centro Comercial El Encuentro');
    expect(loaded.parking.details_en).toContain('15:00');
    expect(loaded.parking.details_en).toContain('01:15');
    expect(loaded.parking.details_en).toContain('20 minutes');
  });

  it('uses a valid cached sheet offline and refreshes it online', async () => {
    const cached: WeddingInfo = {
      ...sheet,
      dress_code: { ...sheet.dress_code, summary: 'Cache ficticio' },
    };
    const storage = memoryStorage(JSON.stringify(cached));
    const offline = await resolveWeddingInfo({ storage, online: false, loaders: {} });
    expect(offline.dress_code.summary).toBe('Cache ficticio');

    const online = await resolveWeddingInfo({ storage, online: true, loaders: {} });
    expect(online.dress_code.summary).toBe(sheet.dress_code.summary);
    expect(storage.getItem('boda-lista.wedding-info')).toContain(sheet.dress_code.summary);
  });
});
