import { beforeEach, describe, expect, it, vi } from 'vitest';
import { clearLastPromptLog, getLastPromptLog } from '../debug/sessionLog';

const mocks = vi.hoisted(() => {
  const generateContent = vi.fn();
  const initializeDeviceModel = vi.fn(() => Promise.resolve());
  const getGenerativeModel = vi.fn(() => ({ generateContent, initializeDeviceModel }));
  const addDoc = vi.fn(async (_ref: unknown, _data?: Record<string, unknown>) => ({ id: 'doc-1' }));
  return { generateContent, initializeDeviceModel, getGenerativeModel, addDoc };
});

vi.mock('firebase/ai', () => ({
  getAI: vi.fn(() => ({})),
  getGenerativeModel: mocks.getGenerativeModel,
  GoogleAIBackend: class GoogleAIBackend {},
  InferenceMode: {
    PREFER_ON_DEVICE: 'prefer_on_device',
    ONLY_ON_DEVICE: 'only_on_device',
    ONLY_IN_CLOUD: 'only_in_cloud',
    PREFER_IN_CLOUD: 'prefer_in_cloud',
  },
  InferenceSource: { ON_DEVICE: 'on_device', IN_CLOUD: 'in_cloud' },
}));

vi.mock('firebase/firestore', () => ({
  addDoc: mocks.addDoc,
  collection: vi.fn(() => ({ path: 'prompt_logs' })),
  getDocs: vi.fn(),
  limit: vi.fn(),
  orderBy: vi.fn(),
  query: vi.fn(),
}));

vi.mock('../firebase/client', () => ({
  getFirebaseApp: vi.fn(() => ({ name: 'app' })),
  getFirestoreDb: vi.fn(() => ({ name: 'db' })),
}));

import { getGenerativeModel, InferenceMode } from 'firebase/ai';
import { ask } from './hybrid';

const PROMPT = 'SECRET_PROMPT_TEXT';
const ANSWER = 'SECRET_ANSWER_TEXT';

function setDevice(status: string | null) {
  if (!status) {
    delete window.LanguageModel;
    return;
  }
  window.LanguageModel = { availability: () => Promise.resolve(status) };
}

function setOnline(online: boolean) {
  Object.defineProperty(window.navigator, 'onLine', { configurable: true, get: () => online });
}

describe('ask', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    clearLastPromptLog();
    setDevice('available');
    setOnline(true);
    mocks.initializeDeviceModel.mockImplementation(() => Promise.resolve());
    mocks.generateContent.mockResolvedValue({
      response: { text: () => ANSWER, inferenceSource: 'on_device' },
    });
    mocks.addDoc.mockResolvedValue({ id: 'doc-1' });
    mocks.getGenerativeModel.mockImplementation(() => ({
      generateContent: mocks.generateContent,
      initializeDeviceModel: mocks.initializeDeviceModel,
    }));
  });

  it('sends online answers to the cloud when no threshold is set', async () => {
    mocks.generateContent.mockImplementation(async () => {
      return { response: { text: () => ANSWER, inferenceSource: 'on_device' } };
    });

    const result = await ask(PROMPT, { feature: 'guest_question', system: 'sistema' });

    expect(getGenerativeModel).toHaveBeenCalledWith(expect.anything(), {
      mode: InferenceMode.ONLY_IN_CLOUD,
      inCloudParams: { model: 'gemini-3.5-flash-lite' },
    });
    expect(result.route).toBe('cloud');
    expect(result.fallbackReason).toBe('no_threshold');
    expect(result.model).toBe('gemini-3.5-flash-lite');
    expect(result.text).toBe(ANSWER);
    const payload = mocks.addDoc.mock.calls[0][1] ?? {};
    expect(Object.keys(payload).sort()).toEqual([
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
    expect(payload.route).toBe('cloud');
    expect(payload.feature).toBe('guest_question');
    expect(payload.fallback_reason).toBe('no_threshold');
    expect(payload.confidence).toBeNull();
    expect(payload.model).toBe('gemini-3.5-flash-lite');
    expect(payload.output_chars).toBe(ANSWER.length);
    expect(payload.input_chars).toBe(`sistema\n\n${PROMPT}`.length);
    expect(String(payload.ts)).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
    const serialized = JSON.stringify(payload);
    expect(serialized).not.toContain(PROMPT);
    expect(serialized).not.toContain(ANSWER);
    expect(getLastPromptLog()).toMatchObject({
      id: 'doc-1',
      route: 'cloud',
      feature: 'guest_question',
      fallback_reason: 'no_threshold',
    });
    expect(JSON.stringify(getLastPromptLog())).not.toContain(PROMPT);
  });

  it('logs the declared lang for a typed guest question', async () => {
    await ask('What time is the ceremony?', { feature: 'guest_question', lang: 'en' });
    const payload = mocks.addDoc.mock.calls[0][1] ?? {};
    expect(payload.lang).toBe('en');
    expect(payload.feature).toBe('guest_question');
    expect(JSON.stringify(payload)).not.toContain('What time');
    expect(getLastPromptLog()?.lang).toBe('en');
  });

  it('answers on device offline when no threshold is set', async () => {
    setOnline(false);
    mocks.generateContent.mockResolvedValue({
      response: { text: () => 'en el teléfono', inferenceSource: 'in_cloud' },
    });
    const result = await ask('hora', { feature: 'guest_question' });
    expect(getGenerativeModel).toHaveBeenCalledWith(expect.anything(), {
      mode: InferenceMode.ONLY_ON_DEVICE,
      inCloudParams: { model: 'gemini-3.5-flash-lite' },
    });
    expect(result.route).toBe('device');
    expect(result.fallbackReason).toBe('offline_no_threshold');
    expect(result.model).toBe('gemini-nano');
    expect(mocks.addDoc.mock.calls[0][1]).toMatchObject({
      route: 'device',
      fallback_reason: 'offline_no_threshold',
    });
  });

  it('returns the answer when the log write fails and still logs a failed call', async () => {
    mocks.addDoc.mockRejectedValueOnce(new Error('denied'));
    const result = await ask(PROMPT, { feature: 'guest_question' });
    expect(result.text).toBe(ANSWER);
    expect(getLastPromptLog()).toBeNull();

    mocks.generateContent.mockRejectedValueOnce(new Error('boom'));
    mocks.addDoc.mockResolvedValueOnce({ id: 'doc-err' });
    await expect(ask(PROMPT, { feature: 'guest_question' })).rejects.toThrow('boom');
    expect(mocks.addDoc.mock.calls.at(-1)?.[1]).toMatchObject({ output_chars: 0 });
    expect(JSON.stringify(mocks.addDoc.mock.calls.at(-1)?.[1])).not.toContain(PROMPT);
  });

  it('reuses one session id', async () => {
    await ask('uno', { feature: 'guest_question' });
    await ask('dos', { feature: 'guest_question' });
    const first = mocks.addDoc.mock.calls[0][1]?.session_id;
    const second = mocks.addDoc.mock.calls[1][1]?.session_id;
    expect(first).toBe(second);
    expect(first).toMatch(/^[0-9a-f-]{8,}$/i);
  });
});
