const SESSION_KEY = 'boda-lista.session-id';

function randomId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `session-${Date.now().toString(16)}-${Math.random().toString(16).slice(2)}`;
}

export function getSessionId(storage: Storage = localStorage): string {
  try {
    const existing = storage.getItem(SESSION_KEY);
    if (existing && existing.trim().length >= 8) return existing;
    const id = randomId();
    storage.setItem(SESSION_KEY, id);
    return id;
  } catch {
    return randomId();
  }
}
