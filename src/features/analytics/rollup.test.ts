import { describe, expect, it } from 'vitest';
import type { FallbackReason, PromptLog, Route } from '../../ai/types';
import { buildRollup, isRollup, percentile } from './rollup';

const NOW = new Date('2026-11-27T12:00:00.000Z');

let counter = 0;
function row(over: Partial<PromptLog> & { route: Route }): PromptLog {
  counter += 1;
  return {
    ts: '2026-11-27T10:00:00.000Z',
    feature: 'guest_question',
    fallback_reason: null,
    latency_ms: 100,
    input_chars: 10,
    output_chars: 20,
    model: over.route === 'sheet' ? null : over.route === 'device' ? 'gemini-nano' : 'gemini-3.5-flash-lite',
    confidence: null,
    session_id: `session-${counter}`,
    ...over,
  };
}

function many(count: number, make: (index: number) => PromptLog): PromptLog[] {
  return Array.from({ length: count }, (_, index) => make(index));
}

describe('percentile', () => {
  it('uses nearest rank and handles empty input', () => {
    expect(percentile([], 50)).toBeNull();
    expect(percentile([5], 95)).toBe(5);
    expect(percentile([10, 20, 30, 40], 50)).toBe(20);
    expect(percentile([40, 10, 30, 20], 95)).toBe(40);
  });
});

describe('buildRollup', () => {
  it('computes device share, cloud calls saved, latency and cloud reasons from AI rows', () => {
    const logs = [
      ...many(20, (i) => row({ route: 'device', latency_ms: 100 + i })),
      ...many(5, () => row({ route: 'cloud', fallback_reason: 'no_model', latency_ms: 900 })),
      ...many(15, () => row({ route: 'cloud', fallback_reason: 'long_input', latency_ms: 1100 })),
    ];
    const { total } = buildRollup(logs, NOW).windows.all;
    expect(total.n).toBe(40);
    expect(total.device_count).toBe(20);
    expect(total.cloud_count).toBe(20);
    expect(total.device_share).toBeCloseTo(0.5);
    expect(total.cloud_calls_saved).toBe(20);
    expect(total.latency_ms.device).toEqual({ p50: 109, p95: 118, n: 20 });
    expect(total.latency_ms.cloud).toEqual({ p50: 1100, p95: 1100, n: 20 });
    expect(total.fallback_reasons).toEqual({ no_model: 5, low_confidence: 0, long_input: 15, no_threshold: 0 });
    expect(total.model_mix).toEqual({ 'gemini-nano': 20, 'gemini-3.5-flash-lite': 20 });
  });

  it('keeps offline_no_threshold rows out of share, saved calls and latency, and counts them on their own', () => {
    const logs = [
      ...many(20, () => row({ route: 'device' })),
      ...many(30, () => row({ route: 'device', fallback_reason: 'offline_no_threshold', latency_ms: 50_000 })),
    ];
    const { total } = buildRollup(logs, NOW).windows.all;
    expect(total.n).toBe(20);
    expect(total.device_share).toBe(1);
    expect(total.cloud_calls_saved).toBe(20);
    expect(total.offline_no_threshold).toBe(30);
    expect(total.latency_ms.device.p95).toBe(100);
  });

  it('keeps sheet answers out of every AI metric and reports them separately', () => {
    const logs = [...many(20, () => row({ route: 'device' })), ...many(40, () => row({ route: 'sheet' }))];
    const { total, by_lang } = buildRollup(logs, NOW).windows.all;
    expect(total.n).toBe(20);
    expect(total.device_share).toBe(1);
    expect(total.sheet_answers).toBe(40);
    expect(total.model_mix).toEqual({ 'gemini-nano': 20 });
    expect(by_lang.unknown.sheet_answers).toBe(40);
    expect(by_lang.unknown.ai_rows).toBe(20);
  });

  it('drops loadtest and eval rows and treats rows without a source as live', () => {
    const logs = [
      ...many(20, () => row({ route: 'device' })),
      ...many(20, () => row({ route: 'cloud', fallback_reason: 'no_model', source: 'loadtest' })),
      ...many(20, () => row({ route: 'cloud', fallback_reason: 'no_model', source: 'eval' })),
      ...many(20, () => row({ route: 'device', source: 'live' })),
    ];
    const rollup = buildRollup(logs, NOW);
    expect(rollup.row_count).toBe(40);
    expect(rollup.windows.all.total.cloud_count).toBe(0);
    expect(rollup.windows.all.total.device_count).toBe(40);
  });

  it('returns null instead of zero below the minimum sample', () => {
    const logs = many(19, () => row({ route: 'device' }));
    const { total } = buildRollup(logs, NOW).windows.all;
    expect(total.n).toBe(19);
    expect(total.device_share).toBeNull();
    expect(total.latency_ms.device).toEqual({ p50: null, p95: null, n: 19 });
    expect(total.cloud_calls_saved).toBe(19);
    expect(buildRollup(logs, NOW, 5).windows.all.total.device_share).toBe(1);
  });

  it('splits by feature and by language, with rows without lang under unknown', () => {
    const logs = [
      ...many(20, () => row({ route: 'device', feature: 'rsvp', lang: 'es' })),
      ...many(20, () => row({ route: 'cloud', feature: 'song', fallback_reason: 'no_threshold', lang: 'en' })),
      ...many(20, () => row({ route: 'device', feature: 'guest_question' })),
    ];
    const { by_feature, by_lang } = buildRollup(logs, NOW).windows.all;
    expect(by_feature.rsvp.device_share).toBe(1);
    expect(by_feature.song.device_share).toBe(0);
    expect(by_feature.guest_question.n).toBe(20);
    expect(by_lang.es.ai_rows).toBe(20);
    expect(by_lang.en.device_share).toBe(0);
    expect(by_lang.unknown.device_share).toBe(1);
    expect(by_lang.unknown.latency_p50_ms).toBe(100);
  });

  it('builds a last 24 hours window', () => {
    const fresh = many(20, () => row({ route: 'device', ts: '2026-11-27T09:00:00.000Z' }));
    const old = many(20, () => row({ route: 'cloud', fallback_reason: 'no_model', ts: '2026-11-25T09:00:00.000Z' }));
    const rollup = buildRollup([...fresh, ...old], NOW);
    expect(rollup.windows.all.total.n).toBe(40);
    expect(rollup.windows.last_24h.total.n).toBe(20);
    expect(rollup.windows.last_24h.total.device_share).toBe(1);
    expect(rollup.generated_at).toBe(NOW.toISOString());
    expect(rollup.source_filter).toBe('live');
  });

  it('reports an empty log with zero counts and null ratios', () => {
    const rollup = buildRollup([], NOW);
    expect(rollup.row_count).toBe(0);
    expect(rollup.windows.all.total.n).toBe(0);
    expect(rollup.windows.all.total.device_share).toBeNull();
    expect(rollup.windows.all.total.offline_no_threshold).toBe(0);
  });

  it('ignores cloud rows whose reason is not a cloud reason', () => {
    const odd: FallbackReason = null;
    const logs = many(20, () => row({ route: 'cloud', fallback_reason: odd }));
    const { total } = buildRollup(logs, NOW).windows.all;
    expect(total.cloud_count).toBe(20);
    expect(Object.values(total.fallback_reasons).reduce((a, b) => a + b, 0)).toBe(0);
  });
});

describe('isRollup', () => {
  it('accepts generated rollups and rejects other JSON', () => {
    expect(isRollup(buildRollup([], NOW))).toBe(true);
    expect(isRollup({ generated_at: 'x' })).toBe(false);
    expect(isRollup(null)).toBe(false);
  });
});
