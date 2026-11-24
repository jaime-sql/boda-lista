import { FEATURES, type FallbackReason, type Feature, type PromptLog, type Route } from '../ai/types';

const STORAGE_KEY = 'boda-lista.last-prompt-log';

export interface LocalPromptLog extends PromptLog {
  id: string;
}

const listeners = new Set<() => void>();
let memory: LocalPromptLog | null = null;

function asRoute(value: unknown): Route | null {
  return value === 'device' || value === 'cloud' || value === 'sheet' ? value : null;
}

function asFeature(value: unknown): Feature | null {
  if (typeof value === 'string' && (FEATURES as readonly string[]).includes(value)) {
    return value as Feature;
  }
  return null;
}

function asFallback(value: unknown): FallbackReason | undefined {
  if (value === null) return null;
  if (
    value === 'no_model' ||
    value === 'low_confidence' ||
    value === 'long_input' ||
    value === 'no_threshold' ||
    value === 'offline_no_threshold'
  ) {
    return value;
  }
  return undefined;
}

function sanitize(value: unknown): LocalPromptLog | null {
  if (!value || typeof value !== 'object') return null;
  const raw = value as Record<string, unknown>;
  const feature = asFeature(raw.feature);
  const route = asRoute(raw.route);
  const fallback = asFallback(raw.fallback_reason);
  if (typeof raw.id !== 'string' || raw.id.length === 0) return null;
  if (!feature || !route || fallback === undefined) return null;
  if (typeof raw.ts !== 'string' || typeof raw.session_id !== 'string') return null;
  if (raw.model !== null && (typeof raw.model !== 'string' || raw.model.length === 0)) return null;
  if (route !== 'sheet' && typeof raw.model !== 'string') return null;
  if (
    typeof raw.latency_ms !== 'number' ||
    typeof raw.input_chars !== 'number' ||
    typeof raw.output_chars !== 'number'
  ) {
    return null;
  }
  const confidence = raw.confidence;
  if (confidence !== null && typeof confidence !== 'number') return null;
  if ('lang' in raw && raw.lang !== 'es' && raw.lang !== 'en') return null;
  if ('edited_by_guest' in raw && typeof raw.edited_by_guest !== 'boolean') return null;
  return {
    id: raw.id,
    ts: raw.ts,
    feature,
    route,
    fallback_reason: fallback,
    latency_ms: raw.latency_ms,
    input_chars: raw.input_chars,
    output_chars: raw.output_chars,
    model: raw.model,
    confidence,
    session_id: raw.session_id,
    ...(raw.lang === 'es' || raw.lang === 'en' ? { lang: raw.lang } : {}),
    ...(typeof raw.edited_by_guest === 'boolean' ? { edited_by_guest: raw.edited_by_guest } : {}),
  };
}

function readStorage(): LocalPromptLog | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return sanitize(JSON.parse(raw) as unknown);
  } catch {
    return null;
  }
}

function notify(): void {
  listeners.forEach((listener) => listener());
}

export function rememberPromptLog(id: string, entry: PromptLog): void {
  const stored = sanitize({ ...entry, id });
  if (!stored) return;
  memory = stored;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
  } catch {
    // The in-memory copy still feeds this tab.
  }
  notify();
}

export function reloadLastPromptLog(): void {
  memory = readStorage() ?? memory;
  notify();
}

export function getLastPromptLog(): LocalPromptLog | null {
  return memory;
}

export function subscribeLastPromptLog(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function markLastPromptDetails(patch: {
  confidence?: number | null;
  edited_by_guest?: boolean;
}): void {
  const current = memory ?? readStorage();
  if (!current) return;
  memory = {
    ...current,
    ...(patch.confidence !== undefined ? { confidence: patch.confidence } : {}),
    ...(patch.edited_by_guest !== undefined ? { edited_by_guest: patch.edited_by_guest } : {}),
  };
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(memory));
  } catch {
    // The in-memory copy still feeds this tab.
  }
  notify();
}

export function clearLastPromptLog(): void {
  memory = null;
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignore storage failures in private mode.
  }
  notify();
}

memory = readStorage();
