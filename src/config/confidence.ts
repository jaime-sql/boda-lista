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

export function thresholdsFor(feature: Feature): FeatureThresholds {
  return confidenceConfig[feature];
}

export function confidenceBand(feature: Feature, value: number): ConfidenceBand {
  const { high, cloud_cutoff } = thresholdsFor(feature);
  if (value >= high) return 'high';
  if (value >= cloud_cutoff) return 'medium';
  return 'low';
}

/** Scores below cloud_cutoff are routed to the cloud model. */
export function isLowConfidence(feature: Feature, value: number): boolean {
  return value < thresholdsFor(feature).cloud_cutoff;
}
