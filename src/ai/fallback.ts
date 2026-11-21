import { isLowConfidence } from '../config/confidence';
import type { DeviceAvailability } from './device';
import type { FallbackReason, Feature, Route } from './types';

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
  feature: Feature;
  deviceStatus: DeviceAvailability;
  inputChars: number;
  confidence: number | null;
}): FallbackReason {
  if (input.route === 'device') return null;
  if (input.deviceStatus !== 'available') return 'no_model';
  if (input.inputChars > ON_DEVICE_INPUT_CHAR_LIMIT) return 'long_input';
  if (input.confidence !== null && isLowConfidence(input.feature, input.confidence)) {
    return 'low_confidence';
  }
  return null;
}
