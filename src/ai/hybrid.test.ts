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

describe('ask', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    clearLastPromptLog();
    setDevice('available');
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

  it('calls prefer_on_device and logs analytics without prompt or answer text', async () => {
    const order: string[] = [];
    mocks.initializeDeviceModel.mockImplementation(() => {
      order.push('init');
      return Promise.resolve();
    });
    mocks.generateContent.mockImplementation(async () => {
      order.push('generate');
      return { response: { text: () => ANSWER, inferenceSource: 'on_device' } };
    });

    const result = await ask(PROMPT, { feature: 'qa', system: 'sistema' });

    expect(order).toEqual(['init', 'generate']);
    expect(getGenerativeModel).toHaveBeenCalledWith(expect.anything(), {
      mode: InferenceMode.PREFER_ON_DEVICE,
      inCloudParams: { model: 'gemini-3.5-flash-lite' },
    });
    expect(result.route).toBe('device');
    expect(result.model).toBe('gemini-nano');
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
    expect(payload.route).toBe('device');
    expect(payload.feature).toBe('qa');
    expect(payload.fallback_reason).toBeNull();
    expect(payload.confidence).toBeNull();
    expect(payload.model).toBe('gemini-nano');
    expect(payload.output_chars).toBe(ANSWER.length);
    expect(payload.input_chars).toBe(`sistema\n\n${PROMPT}`.length);
    expect(String(payload.ts)).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
    const serialized = JSON.stringify(payload);
    expect(serialized).not.toContain(PROMPT);
    expect(serialized).not.toContain(ANSWER);
    expect(getLastPromptLog()).toMatchObject({ id: 'doc-1', route: 'device', feature: 'qa' });
    expect(JSON.stringify(getLastPromptLog())).not.toContain(PROMPT);
  });

  it('records no_model when the SDK uses the cloud and Nano is missing', async () => {
    setDevice(null);
    mocks.generateContent.mockResolvedValue({
      response: { text: () => 'nube', inferenceSource: 'in_cloud' },
    });
    const result = await ask('hora', { feature: 'qa' });
    expect(result.route).toBe('cloud');
    expect(result.model).toBe('gemini-3.5-flash-lite');
    expect(result.fallbackReason).toBe('no_model');
    expect(mocks.addDoc.mock.calls[0][1]).toMatchObject({ route: 'cloud', fallback_reason: 'no_model' });
  });

  it('records long_input and low_confidence from the real cloud route', async () => {
    mocks.generateContent.mockResolvedValue({
      response: { text: () => 'ok', inferenceSource: 'in_cloud' },
    });
    const long = await ask('x'.repeat(8001), { feature: 'songs' });
    expect(long.fallbackReason).toBe('long_input');

    const low = await ask('breve', { feature: 'budget', confidence: 0.2 });
    expect(low.route).toBe('cloud');
    expect(low.fallbackReason).toBe('low_confidence');
    expect(mocks.addDoc.mock.calls[1][1]).toMatchObject({ confidence: 0.2, fallback_reason: 'low_confidence' });
  });

  it('falls back to LanguageModel when the SDK omits inferenceSource', async () => {
    mocks.generateContent.mockResolvedValue({ response: { text: () => 'nano' } });
    const onDevice = await ask('hola', { feature: 'rsvp' });
    expect(onDevice.route).toBe('device');

    setDevice('unavailable');
    const cloud = await ask('hola', { feature: 'seating' });
    expect(cloud.route).toBe('cloud');
    expect(cloud.fallbackReason).toBe('no_model');
  });

  it('returns the answer when the log write fails and still logs a failed call', async () => {
    mocks.addDoc.mockRejectedValueOnce(new Error('denied'));
    const result = await ask(PROMPT, { feature: 'qa' });
    expect(result.text).toBe(ANSWER);
    expect(getLastPromptLog()).toBeNull();

    mocks.generateContent.mockRejectedValueOnce(new Error('boom'));
    mocks.addDoc.mockResolvedValueOnce({ id: 'doc-err' });
    await expect(ask(PROMPT, { feature: 'qa' })).rejects.toThrow('boom');
    expect(mocks.addDoc.mock.calls.at(-1)?.[1]).toMatchObject({ output_chars: 0 });
    expect(JSON.stringify(mocks.addDoc.mock.calls.at(-1)?.[1])).not.toContain(PROMPT);
  });

  it('reuses one session id', async () => {
    await ask('uno', { feature: 'qa' });
    await ask('dos', { feature: 'qa' });
    const first = mocks.addDoc.mock.calls[0][1]?.session_id;
    const second = mocks.addDoc.mock.calls[1][1]?.session_id;
    expect(first).toBe(second);
    expect(first).toMatch(/^[0-9a-f-]{8,}$/i);
  });
});
