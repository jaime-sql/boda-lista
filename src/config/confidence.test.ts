import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { FEATURES } from '../ai/types';
import config from './config.json';
import { confidenceBand, confidenceConfig, isLowConfidence, thresholdsFor } from './confidence';

type SchemaTask = { properties?: { task?: { const?: string } } };

function schemaTaskConstants(): string[] {
  const schema = JSON.parse(readFileSync(join(process.cwd(), 'data/schema.json'), 'utf8')) as {
    $defs?: Record<string, SchemaTask>;
  };
  const tasks = Object.values(schema.$defs ?? {})
    .map((definition) => definition.properties?.task?.const)
    .filter((task): task is string => typeof task === 'string');
  return [...new Set(tasks)].sort();
}

describe('confidence config', () => {
  it('uses the schema task keys and no aliases', () => {
    const tasks = schemaTaskConstants();
    expect(tasks).toEqual(['guest_question', 'rsvp', 'song']);
    const configKeys = Object.keys(config)
      .filter((key) => key !== 'analytics')
      .sort();
    expect(configKeys).toEqual(tasks);
    expect([...FEATURES].sort()).toEqual(tasks);
    expect(configKeys).not.toEqual(expect.arrayContaining(['qa', 'songs', 'budget', 'seating']));
    expect(confidenceConfig.analytics.min_sample).toBe(20);
    expect(confidenceConfig.guest_question).toEqual({ high: null, cloud_cutoff: null, min_n: 20 });
    expect(confidenceConfig.rsvp.high).toBeNull();
    expect(confidenceConfig.song.cloud_cutoff).toBeNull();
    expect(confidenceBand('guest_question', 0.99)).toBeNull();
    expect(isLowConfidence('guest_question', 0.1)).toBe(false);
  });

  it('throws for an unknown feature key', () => {
    expect(() => thresholdsFor('qa')).toThrow(/unknown feature: qa/);
    expect(() => thresholdsFor('songs')).toThrow(/unknown feature: songs/);
    expect(() => thresholdsFor('budget')).toThrow(/unknown feature: budget/);
    expect(() => confidenceBand('seating', 0.9)).toThrow(/unknown feature: seating/);
    expect(() => isLowConfidence('analytics', 0.1)).toThrow(/unknown feature: analytics/);
  });
});
