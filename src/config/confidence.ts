import type { Feature } from '../ai/types';
import config from './config.json';

export interface FeatureThresholds {
  high: number;
  cloud_cutoff: number;
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

export function confidenceBand(feature: string, value: number): ConfidenceBand {
  const { high, cloud_cutoff } = thresholdsFor(feature);
  if (value >= high) return 'high';
  if (value >= cloud_cutoff) return 'medium';
  return 'low';
}

/** Scores below cloud_cutoff are routed to the cloud model. */
export function isLowConfidence(feature: string, value: number): boolean {
  return value < thresholdsFor(feature).cloud_cutoff;
}
