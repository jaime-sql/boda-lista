import { describe, expect, it } from 'vitest';
import { confidenceBand, cutoffsFor, isLowConfidence } from './confidence';

describe('confidence bands', () => {
  it('uses one default and per-feature cut-offs', () => {
    expect(cutoffsFor('qa')).toEqual({ high: 0.85, medium: 0.6 });
    expect(cutoffsFor('rsvp')).toEqual(cutoffsFor('qa'));
    expect(cutoffsFor('songs')).toEqual(cutoffsFor('qa'));
    expect(cutoffsFor('budget')).toEqual({ high: 0.85, medium: 0.6 });
    expect(cutoffsFor('seating')).toEqual(cutoffsFor('budget'));
  });

  it('bands a score without leaving the numbers in the caller', () => {
    expect(confidenceBand('qa', 0.85)).toBe('high');
    expect(confidenceBand('rsvp', 0.6)).toBe('medium');
    expect(confidenceBand('songs', 0.59)).toBe('low');
    expect(isLowConfidence('qa', 0.2)).toBe(true);
    expect(isLowConfidence('qa', 0.6)).toBe(false);
  });
});
