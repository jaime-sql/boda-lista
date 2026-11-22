import type { DeviceAvailability } from './device';
import type { FallbackReason, Route } from './types';

export const ON_DEVICE_INPUT_CHAR_LIMIT = 8000;
export const ON_DEVICE_MODEL_NAME = 'gemini-nano';
export const DEFAULT_CLOUD_MODEL = 'gemini-3.5-flash-lite';

export function cloudModelName(override?: string): string {
  const fromEnv = override ?? import.meta.env.VITE_GEMINI_CLOUD_MODEL;
  const trimmed = fromEnv?.trim();
  return trimmed ? trimmed : DEFAULT_CLOUD_MODEL;
}

export function normalizeConfidence(value: number | null | undefined): number | null {
  if (typeof value !== 'number' || !Number.isFinite(value)) return null;
  return value;
}

export function routeFromInference(
  source: string | undefined,
  deviceStatus: DeviceAvailability,
): Route {
  if (source === 'on_device') return 'device';
  if (source === 'in_cloud') return 'cloud';
  return deviceStatus === 'available' ? 'device' : 'cloud';
}

export function classifyFallback(input: {
  route: Route;
  deviceStatus: DeviceAvailability;
  inputChars: number;
  confidence: number | null;
  cloudCutoff: number | null;
}): FallbackReason {
  if (input.route === 'device') return null;
  if (input.deviceStatus !== 'available') return 'no_model';
  if (input.inputChars > ON_DEVICE_INPUT_CHAR_LIMIT) return 'long_input';
  if (
    input.cloudCutoff !== null &&
    input.confidence !== null &&
    input.confidence < input.cloudCutoff
  ) {
    return 'low_confidence';
  }
  return null;
}

export function planRoute(input: {
  online: boolean;
  high: number | null;
  cloudCutoff: number | null;
  confidence: number | null;
  inferenceSource?: string;
  deviceStatus: DeviceAvailability;
  inputChars: number;
}): { mode: 'prefer_on_device' | 'only_in_cloud' | 'only_on_device'; route: Route; reason: FallbackReason } {
  if (input.high === null || input.cloudCutoff === null) {
    if (input.online) {
      return { mode: 'only_in_cloud', route: 'cloud', reason: 'no_threshold' };
    }
    return { mode: 'only_on_device', route: 'device', reason: 'offline_no_threshold' };
  }
  let route = routeFromInference(input.inferenceSource, input.deviceStatus);
  let mode: 'prefer_on_device' | 'only_in_cloud' = 'prefer_on_device';
  if (input.confidence !== null && input.confidence < input.cloudCutoff) {
    route = 'cloud';
    mode = 'only_in_cloud';
  }
  return {
    mode,
    route,
    reason: classifyFallback({
      route,
      deviceStatus: input.deviceStatus,
      inputChars: input.inputChars,
      confidence: input.confidence,
      cloudCutoff: input.cloudCutoff,
    }),
  };
}
