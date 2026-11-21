import { getAI, getGenerativeModel, GoogleAIBackend, InferenceMode } from 'firebase/ai';
import { probeDeviceModel } from './device';
import {
  classifyFallback,
  cloudModelName,
  normalizeConfidence,
  ON_DEVICE_MODEL_NAME,
  routeFromInference,
} from './fallback';
import type { AskContext, AskResult, Feature, PromptLog } from './types';
import { FEATURES } from './types';
import { rememberPromptLog } from '../debug/sessionLog';
import { getFirebaseApp } from '../firebase/client';
import { writePromptLog } from '../firebase/logs';
import { getSessionId } from '../lib/session';

type ModelResponse = {
  text?: (() => string) | string;
  inferenceSource?: string;
};

type HybridModel = {
  initializeDeviceModel: (onProgress?: (value: number) => void) => Promise<void> | void;
  generateContent: (prompt: string) => Promise<{ response: ModelResponse }>;
};

function isFeature(value: string): value is Feature {
  return (FEATURES as readonly string[]).includes(value);
}

function readText(response: ModelResponse): string {
  if (typeof response.text === 'function') return response.text();
  if (typeof response.text === 'string') return response.text;
  return '';
}

function composePrompt(prompt: string, system?: string): string {
  if (!system) return prompt;
  return `${system}\n\n${prompt}`;
}

async function safeLog(entry: PromptLog): Promise<void> {
  try {
    const id = await writePromptLog(entry);
    rememberPromptLog(id, entry);
  } catch {
    console.error('prompt_logs write failed');
  }
}

export async function ask(prompt: string, context: AskContext): Promise<AskResult> {
  if (!isFeature(context.feature)) {
    throw new Error('feature-invalid');
  }

  const fullPrompt = composePrompt(prompt, context.system);
  const inputChars = fullPrompt.length;
  const confidence = normalizeConfidence(context.confidence);
  const sessionId = getSessionId();
  const cloudModel = cloudModelName();
  const app = getFirebaseApp();
  const ai = getAI(app, { backend: new GoogleAIBackend() });
  const model = getGenerativeModel(ai, {
    mode: InferenceMode.PREFER_ON_DEVICE,
    inCloudParams: { model: cloudModel },
  }) as HybridModel;

  try {
    const pendingInit = model.initializeDeviceModel(() => undefined);
    void Promise.resolve(pendingInit).catch(() => undefined);
  } catch {
    // Cloud fallback still runs when the on-device model cannot start.
  }

  const started = performance.now();
  const generation = model.generateContent(fullPrompt);
  const deviceStatusPromise = probeDeviceModel();

  try {
    const result = await generation;
    const latencyMs = Math.max(0, Math.round(performance.now() - started));
    const text = readText(result.response);
    const deviceStatus = await deviceStatusPromise;
    const route = routeFromInference(result.response.inferenceSource, deviceStatus);
    const fallbackReason = classifyFallback({
      route,
      deviceStatus,
      inputChars,
      confidence,
    });
    const modelName = route === 'device' ? ON_DEVICE_MODEL_NAME : cloudModel;
    await safeLog({
      ts: new Date().toISOString(),
      feature: context.feature,
      route,
      fallback_reason: fallbackReason,
      latency_ms: latencyMs,
      input_chars: inputChars,
      output_chars: text.length,
      model: modelName,
      confidence,
      session_id: sessionId,
    });
    return {
      text,
      route,
      fallbackReason,
      latencyMs,
      inputChars,
      outputChars: text.length,
      model: modelName,
    };
  } catch (error) {
    const latencyMs = Math.max(0, Math.round(performance.now() - started));
    const deviceStatus = await deviceStatusPromise;
    const route = 'cloud' as const;
    const fallbackReason = classifyFallback({
      route,
      deviceStatus,
      inputChars,
      confidence,
    });
    await safeLog({
      ts: new Date().toISOString(),
      feature: context.feature,
      route,
      fallback_reason: fallbackReason,
      latency_ms: latencyMs,
      input_chars: inputChars,
      output_chars: 0,
      model: cloudModel,
      confidence,
      session_id: sessionId,
    });
    throw error;
  }
}
