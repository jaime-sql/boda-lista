import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { clearLastPromptLog, getLastPromptLog } from '../debug/sessionLog';

const mocks = vi.hoisted(() => ({
  missingEnv: vi.fn((): string[] => ['VITE_FIREBASE_API_KEY']),
  writePromptLog: vi.fn(async (_entry: Record<string, unknown>) => 'doc-sheet'),
  getGenerativeModel: vi.fn(),
}));

vi.mock('../firebase/config', () => ({
  missingEnv: mocks.missingEnv,
}));

vi.mock('../firebase/logs', () => ({
  writePromptLog: mocks.writePromptLog,
}));

vi.mock('firebase/ai', () => ({
  getAI: vi.fn(),
  getGenerativeModel: mocks.getGenerativeModel,
  GoogleAIBackend: class GoogleAIBackend {},
  InferenceMode: { ONLY_IN_CLOUD: 'only_in_cloud' },
}));

import { getGenerativeModel } from 'firebase/ai';
import { logSheetDecision } from './sheetLog';

describe('sheet decision log', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    clearLastPromptLog();
    mocks.missingEnv.mockReturnValue(['VITE_FIREBASE_API_KEY']);
    mocks.writePromptLog.mockResolvedValue('doc-sheet');
  });

  it('keeps a local sheet row and skips Firestore when Firebase is absent', async () => {
    await logSheetDecision(18);
    expect(mocks.writePromptLog).not.toHaveBeenCalled();
    expect(getGenerativeModel).not.toHaveBeenCalled();
    expect(getLastPromptLog()).toMatchObject({
      id: 'sheet-local',
      feature: 'guest_question',
      route: 'sheet',
      model: null,
      fallback_reason: null,
      input_chars: 0,
      output_chars: 18,
      confidence: null,
    });
  });

  it('writes route sheet and model null when Firebase is configured', async () => {
    mocks.missingEnv.mockReturnValue([]);
    await logSheetDecision(24);
    expect(getGenerativeModel).not.toHaveBeenCalled();
    expect(mocks.writePromptLog).toHaveBeenCalledTimes(1);
    const entry = mocks.writePromptLog.mock.calls[0][0];
    expect(Object.keys(entry).sort()).toEqual([
      'confidence',
      'fallback_reason',
      'feature',
      'input_chars',
      'latency_ms',
      'model',
      'output_chars',
      'route',
      'session_id',
      'ts',
    ]);
    expect(entry).toMatchObject({
      feature: 'guest_question',
      route: 'sheet',
      model: null,
      fallback_reason: null,
      input_chars: 0,
      output_chars: 24,
      confidence: null,
      latency_ms: 0,
    });
    expect(JSON.stringify(entry)).toContain('"model":null');
    expect(JSON.stringify(entry)).not.toContain('"none"');
    expect(JSON.stringify(entry)).not.toContain('Horario');
    expect(JSON.stringify(entry)).not.toContain('16:00');
    expect(getLastPromptLog()).toMatchObject({ id: 'doc-sheet', route: 'sheet', model: null });
  });

  it('still records sheet when the log write fails', async () => {
    mocks.missingEnv.mockReturnValue([]);
    mocks.writePromptLog.mockRejectedValueOnce(new Error('denied'));
    await logSheetDecision(4);
    expect(getGenerativeModel).not.toHaveBeenCalled();
    expect(getLastPromptLog()).toMatchObject({ route: 'sheet', model: null, output_chars: 4 });
  });

  it('allows sheet in the prompt_logs rules', () => {
    const rules = readFileSync(join(process.cwd(), 'firestore.rules'), 'utf8');
    expect(rules).toContain("data.route in ['device', 'cloud', 'sheet']");
    expect(rules).toContain("data.route == 'sheet' && data.model == null");
  });
});
