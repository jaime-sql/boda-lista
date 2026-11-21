import type { Feature } from '../ai/types';

export interface ConfidenceCutoffs {
  /** Inclusive lower bound for the high band. */
  high: number;
  /** Inclusive lower bound for the medium band. Anything below is low. */
  medium: number;
}

export const DEFAULT_CONFIDENCE_CUTOFFS: ConfidenceCutoffs = {
  high: 0.85,
  medium: 0.6,
};

export const CONFIDENCE_CUTOFFS: Partial<Record<Feature, ConfidenceCutoffs>> = {
  qa: { high: 0.85, medium: 0.6 },
  rsvp: { high: 0.85, medium: 0.6 },
  songs: { high: 0.85, medium: 0.6 },
};

export type ConfidenceBand = 'high' | 'medium' | 'low';

export function cutoffsFor(feature: Feature): ConfidenceCutoffs {
  return CONFIDENCE_CUTOFFS[feature] ?? DEFAULT_CONFIDENCE_CUTOFFS;
}

export function confidenceBand(feature: Feature, value: number): ConfidenceBand {
  const cutoffs = cutoffsFor(feature);
  if (value >= cutoffs.high) return 'high';
  if (value >= cutoffs.medium) return 'medium';
  return 'low';
}

export function isLowConfidence(feature: Feature, value: number): boolean {
  return confidenceBand(feature, value) === 'low';
}
