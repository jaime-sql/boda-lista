import { getAI, getGenerativeModel, GoogleAIBackend, InferenceMode } from 'firebase/ai';
import { probeDeviceModel } from './device';
import { classifyFallback, cloudModelName, normalizeConfidence, ON_DEVICE_MODEL_NAME, planRoute } from './fallback';
import { thresholdsFor } from '../config/confidence';
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
  const thresholds = thresholdsFor(context.feature);
  const online = typeof navigator === 'undefined' || navigator.onLine !== false;
  const app = getFirebaseApp();
  const ai = getAI(app, { backend: new GoogleAIBackend() });
  const deviceStatusPromise = probeDeviceModel();
  const deviceStatus = await deviceStatusPromise;
  let plan = planRoute({
    online,
    high: thresholds.high,
    cloudCutoff: thresholds.cloud_cutoff,
    confidence,
    deviceStatus,
    inputChars,
  });
  if (context.forceCloud && online) {
    const noThreshold = thresholds.high === null || thresholds.cloud_cutoff === null;
    plan = {
      mode: 'only_in_cloud',
      route: 'cloud',
      reason: noThreshold
        ? 'no_threshold'
        : classifyFallback({
            route: 'cloud',
            deviceStatus,
            inputChars,
            confidence,
            cloudCutoff: thresholds.cloud_cutoff,
          }),
    };
  }
  const mode =
    plan.mode === 'only_in_cloud'
      ? InferenceMode.ONLY_IN_CLOUD
      : plan.mode === 'only_on_device'
        ? InferenceMode.ONLY_ON_DEVICE
        : InferenceMode.PREFER_ON_DEVICE;
  const model = getGenerativeModel(ai, {
    mode,
    inCloudParams: { model: cloudModel },
  }) as HybridModel;

  if (plan.mode !== 'only_in_cloud') {
    try {
      const pendingInit = model.initializeDeviceModel(() => undefined);
      void Promise.resolve(pendingInit).catch(() => undefined);
    } catch {
      // Cloud fallback still runs when the on-device model cannot start.
    }
  }

  const started = performance.now();
  const generation = model.generateContent(fullPrompt);

  try {
    const result = await generation;
    const latencyMs = Math.max(0, Math.round(performance.now() - started));
    const text = readText(result.response);
    let settled = planRoute({
      online,
      high: thresholds.high,
      cloudCutoff: thresholds.cloud_cutoff,
      confidence,
      inferenceSource: result.response.inferenceSource,
      deviceStatus,
      inputChars,
    });
    if (context.forceCloud && online) {
      const noThreshold = thresholds.high === null || thresholds.cloud_cutoff === null;
      settled = {
        mode: 'only_in_cloud',
        route: 'cloud',
        reason: noThreshold ? 'no_threshold' : settled.reason,
      };
    }
    const route = settled.route;
    const fallbackReason = settled.reason;
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
      ...(context.feature === 'rsvp' ? { edited_by_guest: false } : {}),
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
    const route = plan.route;
    const fallbackReason = plan.reason;
    await safeLog({
      ts: new Date().toISOString(),
      feature: context.feature,
      route,
      fallback_reason: fallbackReason,
      latency_ms: latencyMs,
      input_chars: inputChars,
      output_chars: 0,
      model: route === 'device' ? ON_DEVICE_MODEL_NAME : cloudModel,
      confidence,
      session_id: sessionId,
      ...(context.feature === 'rsvp' ? { edited_by_guest: false } : {}),
    });
    throw error;
  }
}
