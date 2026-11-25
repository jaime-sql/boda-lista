import sample from './wedding_info.sample.json';
import type { WeddingInfo } from './types';

const CACHE_KEY = 'boda-lista.wedding-info';

export const SAMPLE_SHEET_MODULE = 'src/data/wedding_info.sample.json';
export const PACK_SHEET_PATH = 'data/wedding_info.json';

export type SheetOrigin = 'sample' | 'pack';

type PackModule = { default: unknown };
type PackLoader = () => Promise<PackModule>;

const packLoaders = import.meta.glob<PackModule>('../../data/wedding_info.json');

const fallbackSheet = sample as WeddingInfo;

function isOptionalString(value: unknown): boolean {
  return value === undefined || typeof value === 'string';
}

export function isWeddingInfo(value: unknown): value is WeddingInfo {
  if (!value || typeof value !== 'object') return false;
  const sheet = value as WeddingInfo;
  return (
    sheet.synthetic === true &&
    typeof sheet.disclaimer === 'string' &&
    typeof sheet.couple?.bride?.first_name === 'string' &&
    typeof sheet.couple?.groom?.first_name === 'string' &&
    typeof sheet.date === 'string' &&
    typeof sheet.timezone === 'string' &&
    Array.isArray(sheet.schedule) &&
    typeof sheet.venue?.name === 'string' &&
    typeof sheet.venue?.address === 'string' &&
    typeof sheet.venue?.city === 'string' &&
    typeof sheet.venue?.country === 'string' &&
    isOptionalString(sheet.venue?.notes) &&
    isOptionalString(sheet.venue?.notes_es) &&
    typeof sheet.dress_code?.summary === 'string' &&
    typeof sheet.parking?.summary === 'string' &&
    isOptionalString(sheet.parking?.details) &&
    isOptionalString(sheet.parking?.details_en) &&
    typeof sheet.gifts?.summary === 'string' &&
    Array.isArray(sheet.contacts)
  );
}

export function activeSheetOrigin(
  loaders: Record<string, PackLoader> = packLoaders,
): SheetOrigin {
  return Object.keys(loaders).length > 0 ? 'pack' : 'sample';
}

export async function loadFromLoaders(
  loaders: Record<string, PackLoader>,
  fallback: WeddingInfo = fallbackSheet,
): Promise<WeddingInfo> {
  const load = Object.values(loaders)[0];
  if (!load) return fallback;
  try {
    const loaded = await load();
    if (isWeddingInfo(loaded.default)) return loaded.default;
  } catch {
    // A missing or unreadable pack falls back to the bundled sample.
  }
  return fallback;
}

export async function loadBundledWeddingInfo(): Promise<WeddingInfo> {
  return loadFromLoaders(packLoaders, fallbackSheet);
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
  loaders?: Record<string, PackLoader>;
}): Promise<WeddingInfo> {
  const storage = options?.storage ?? localStorage;
  const online = options?.online ?? navigator.onLine;
  if (!online) {
    const cached = readCache(storage);
    if (cached) return cached;
  }
  const bundled = await loadFromLoaders(options?.loaders ?? packLoaders, fallbackSheet);
  writeCache(storage, bundled);
  return bundled;
}
