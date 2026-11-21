import type { Feature } from '../ai/types';
import config from './config.json';

export interface FeatureThresholds {
  high: number | null;
  cloud_cutoff: number | null;
  min_n: number;
}

export interface AnalyticsThresholds {
  min_sample: number;
}

export interface ConfidenceConfig {
  guest_question: FeatureThresholds;
  rsvp: FeatureThresholds;
  song: FeatureThresholds;
  analytics: AnalyticsThresholds;
}

export const confidenceConfig = config as ConfidenceConfig;

export type ConfidenceBand = 'high' | 'medium' | 'low';

function isFeatureKey(feature: string): feature is Feature {
  const row = (confidenceConfig as unknown as Record<string, unknown>)[feature];
  return (
    !!row &&
    typeof row === 'object' &&
    'high' in row &&
    'cloud_cutoff' in row &&
    'min_n' in row
  );
}

export function thresholdsFor(feature: string): FeatureThresholds {
  if (!isFeatureKey(feature)) {
    throw new Error(`unknown feature: ${feature}`);
  }
  return confidenceConfig[feature];
}

export function hasThreshold(
  thresholds: Pick<FeatureThresholds, 'high' | 'cloud_cutoff'>,
): thresholds is { high: number; cloud_cutoff: number } {
  return typeof thresholds.high === 'number' && typeof thresholds.cloud_cutoff === 'number';
}

export function confidenceBand(feature: string, value: number): ConfidenceBand | null {
  const thresholds = thresholdsFor(feature);
  if (!hasThreshold(thresholds)) return null;
  if (value >= thresholds.high) return 'high';
  if (value >= thresholds.cloud_cutoff) return 'medium';
  return 'low';
}

/** Scores below cloud_cutoff are routed to the cloud model. Null cutoffs are not a band. */
export function isLowConfidence(feature: string, value: number): boolean {
  const thresholds = thresholdsFor(feature);
  if (!hasThreshold(thresholds)) return false;
  return value < thresholds.cloud_cutoff;
}
