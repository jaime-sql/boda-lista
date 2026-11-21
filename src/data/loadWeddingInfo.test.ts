import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import sample from './wedding_info.sample.json';
import { PACK_SHEET_PATH, activeSheetOrigin, resolveWeddingInfo } from './loadWeddingInfo';

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
  it('points at the future pack without importing it', () => {
    expect(activeSheetOrigin()).toBe('sample');
    expect(PACK_SHEET_PATH).toBe('data/wedding_info.json');
    const source = readFileSync(join(process.cwd(), 'src/data/loadWeddingInfo.ts'), 'utf8');
    expect(source).not.toContain("import('../../data/wedding_info.json')");
    expect(source).not.toContain('from \'../../../data/wedding_info.json\'');
  });

  it('uses the cached sheet offline and refreshes it online', async () => {
    const cached = { ...sample, dress_code: 'Cache ficticio' };
    const storage = memoryStorage(JSON.stringify(cached));
    const offline = await resolveWeddingInfo({ storage, online: false });
    expect(offline.dress_code).toBe('Cache ficticio');

    const online = await resolveWeddingInfo({ storage, online: true });
    expect(online.dress_code).toBe(sample.dress_code);
    expect(storage.getItem('boda-lista.wedding-info')).toContain(sample.dress_code);
  });
});
