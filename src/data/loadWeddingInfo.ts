import sample from './wedding_info.sample.json';
import type { WeddingInfo } from './types';

const CACHE_KEY = 'boda-lista.wedding-info';

/** Bundled sample used today. */
export const SAMPLE_SHEET_MODULE = 'src/data/wedding_info.sample.json';

/**
 * Shared data pack added by a later change.
 * Point `loadBundledWeddingInfo` at this path when the file exists.
 * It is not imported yet, so the app builds without a top-level data/ directory.
 */
export const PACK_SHEET_PATH = 'data/wedding_info.json';

export type SheetOrigin = 'sample' | 'pack';

export function activeSheetOrigin(): SheetOrigin {
  return 'sample';
}

export async function loadBundledWeddingInfo(): Promise<WeddingInfo> {
  const origin = activeSheetOrigin();
  if (origin === 'sample') {
    return sample as WeddingInfo;
  }
  throw new Error(`The sheet at ${PACK_SHEET_PATH} is not wired yet.`);
}

function isWeddingInfo(value: unknown): value is WeddingInfo {
  if (!value || typeof value !== 'object') return false;
  const sheet = value as WeddingInfo;
  return (
    Array.isArray(sheet.schedule) &&
    typeof sheet.dress_code === 'string' &&
    typeof sheet.venue?.name === 'string' &&
    typeof sheet.parking === 'string' &&
    typeof sheet.gifts === 'string' &&
    Array.isArray(sheet.contacts)
  );
}

function readCache(storage: Storage): WeddingInfo | null {
  try {
    const raw = storage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    return isWeddingInfo(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function writeCache(storage: Storage, info: WeddingInfo): void {
  try {
    storage.setItem(CACHE_KEY, JSON.stringify(info));
  } catch {
    // Private mode and full storage still leave the bundled sheet usable.
  }
}

export async function resolveWeddingInfo(options?: {
  storage?: Storage;
  online?: boolean;
}): Promise<WeddingInfo> {
  const storage = options?.storage ?? localStorage;
  const online = options?.online ?? navigator.onLine;
  if (!online) {
    const cached = readCache(storage);
    if (cached) return cached;
  }
  const bundled = await loadBundledWeddingInfo();
  writeCache(storage, bundled);
  return bundled;
}
