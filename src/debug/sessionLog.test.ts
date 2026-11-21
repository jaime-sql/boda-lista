import { beforeEach, describe, expect, it } from 'vitest';
import { clearLastPromptLog, getLastPromptLog, reloadLastPromptLog, rememberPromptLog } from './sessionLog';

const entry = {
  ts: '2026-11-21T18:00:00.000Z',
  feature: 'qa' as const,
  route: 'device' as const,
  fallback_reason: null,
  latency_ms: 12,
  input_chars: 40,
  output_chars: 8,
  model: 'gemini-nano',
  confidence: null,
  session_id: 'session-abc12345',
};

describe('local prompt log', () => {
  beforeEach(() => {
    clearLastPromptLog();
  });

  it('keeps the doc id and analytics fields only', () => {
    rememberPromptLog('doc-1', entry);
    expect(getLastPromptLog()).toEqual({ id: 'doc-1', ...entry });
    expect(JSON.stringify(getLastPromptLog())).not.toContain('pregunta');
  });

  it('drops prompt text that was stuffed into session storage', () => {
    sessionStorage.setItem(
      'boda-lista.last-prompt-log',
      JSON.stringify({
        ...entry,
        id: 'doc-2',
        prompt: 'SECRET_PROMPT',
        response: 'SECRET_ANSWER',
        guest: 'Invitado Real',
      }),
    );
    reloadLastPromptLog();
    const stored = getLastPromptLog();
    expect(stored?.id).toBe('doc-2');
    expect(JSON.stringify(stored)).not.toContain('SECRET_PROMPT');
    expect(JSON.stringify(stored)).not.toContain('SECRET_ANSWER');
    expect(JSON.stringify(stored)).not.toContain('Invitado Real');
  });
});
