import { describe, expect, it } from 'vitest';
import { thresholdsFor } from '../../config/confidence';
import { planRoute } from '../../ai/fallback';
import { parseRsvpOutput, sameExtraction } from './parse';

const valid = {
  attending: 'yes',
  party_size: 3,
  meal_restrictions: ['vegetarian', 'allergy:mani'],
  kids_count: 1,
  needs_ride: true,
  ambiguous: false,
  confidence: 0.8,
};

describe('rsvp parsing', () => {
  it('accepts schema-shaped JSON and fenced JSON', () => {
    expect(parseRsvpOutput(JSON.stringify(valid))?.party_size).toBe(3);
    expect(parseRsvpOutput('```json\n' + JSON.stringify(valid) + '\n```')?.attending).toBe('yes');
    expect(parseRsvpOutput(JSON.stringify({ ...valid, party_size: null, kids_count: null, needs_ride: null }))).toMatchObject({
      party_size: null,
      kids_count: null,
      needs_ride: null,
    });
  });

  it('rejects invalid meals, counts, and broken JSON', () => {
    expect(parseRsvpOutput('no es json')).toBeNull();
    expect(parseRsvpOutput(JSON.stringify({ ...valid, meal_restrictions: ['pescado'] }))).toBeNull();
    expect(parseRsvpOutput(JSON.stringify({ ...valid, party_size: 0 }))).toBeNull();
    expect(parseRsvpOutput(JSON.stringify({ ...valid, attending: 'maybe-not' }))).toBeNull();
    expect(parseRsvpOutput(JSON.stringify({ ...valid, confidence: 2 }))).toBeNull();
  });

  it('routes the rsvp key and throws for an unknown key', () => {
    expect(thresholdsFor('rsvp').min_n).toBe(20);
    expect(() => thresholdsFor('qa')).toThrow(/unknown feature: qa/);
    const online = planRoute({
      online: true,
      high: null,
      cloudCutoff: null,
      confidence: 0.4,
      deviceStatus: 'available',
      inputChars: 40,
    });
    expect(online).toMatchObject({ route: 'cloud', reason: 'no_threshold' });
    const offline = planRoute({
      online: false,
      high: null,
      cloudCutoff: null,
      confidence: null,
      deviceStatus: 'unavailable',
      inputChars: 40,
    });
    expect(offline).toMatchObject({ route: 'device', reason: 'offline_no_threshold' });
    const scored = planRoute({
      online: true,
      high: 0.85,
      cloudCutoff: 0.6,
      confidence: 0.2,
      inferenceSource: 'on_device',
      deviceStatus: 'available',
      inputChars: 40,
    });
    expect(scored.route).toBe('cloud');
    expect(scored.reason).toBe('low_confidence');
  });

  it('detects guest edits without comparing the message', () => {
    const parsed = parseRsvpOutput(JSON.stringify(valid));
    expect(parsed).not.toBeNull();
    if (!parsed) return;
    expect(sameExtraction(parsed, { ...parsed })).toBe(true);
    expect(sameExtraction(parsed, { ...parsed, party_size: 2 })).toBe(false);
  });
});
