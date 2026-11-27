import { FEATURES, type Feature, type PromptLog } from '../../ai/types';
import { confidenceConfig } from '../../config/confidence';

export const CLOUD_REASONS = ['no_model', 'low_confidence', 'long_input', 'no_threshold'] as const;
export type CloudReason = (typeof CLOUD_REASONS)[number];

export interface LatencyCell {
  p50: number | null;
  p95: number | null;
  n: number;
}

export interface RollupCell {
  /** AI rows that count toward device share: route is device or cloud, and not offline_no_threshold. */
  n: number;
  device_count: number;
  cloud_count: number;
  device_share: number | null;
  cloud_calls_saved: number;
  latency_ms: { device: LatencyCell; cloud: LatencyCell };
  fallback_reasons: Record<CloudReason, number>;
  model_mix: Record<string, number>;
  offline_no_threshold: number;
  sheet_answers: number;
}

export interface LangCell {
  ai_rows: number;
  device_share: number | null;
  latency_p50_ms: number | null;
  latency_p95_ms: number | null;
  sheet_answers: number;
}

export type LangKey = 'es' | 'en' | 'unknown';

export interface RollupWindow {
  total: RollupCell;
  by_feature: Record<Feature, RollupCell>;
  by_lang: Record<LangKey, LangCell>;
}

export interface Rollup {
  generated_at: string;
  source_filter: 'live';
  row_count: number;
  min_sample: number;
  windows: { all: RollupWindow; last_24h: RollupWindow };
}

const DAY_MS = 24 * 60 * 60 * 1000;

/** Nearest-rank percentile on an unsorted list. */
export function percentile(values: number[], p: number): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const rank = Math.max(1, Math.ceil((p / 100) * sorted.length));
  return sorted[rank - 1] ?? null;
}

function latencyCell(values: number[], minSample: number): LatencyCell {
  if (values.length < minSample) return { p50: null, p95: null, n: values.length };
  return { p50: percentile(values, 50), p95: percentile(values, 95), n: values.length };
}

function isLive(log: PromptLog): boolean {
  return log.source === undefined || log.source === 'live';
}

function isCountedAi(log: PromptLog): boolean {
  return log.route !== 'sheet' && log.fallback_reason !== 'offline_no_threshold';
}

function buildCell(rows: PromptLog[], minSample: number): RollupCell {
  const sheet = rows.filter((row) => row.route === 'sheet');
  const ai = rows.filter((row) => row.route !== 'sheet');
  const counted = ai.filter(isCountedAi);
  const device = counted.filter((row) => row.route === 'device');
  const cloud = counted.filter((row) => row.route === 'cloud');

  const fallbackReasons: Record<CloudReason, number> = {
    no_model: 0,
    low_confidence: 0,
    long_input: 0,
    no_threshold: 0,
  };
  for (const row of cloud) {
    const reason = row.fallback_reason;
    if (reason && (CLOUD_REASONS as readonly string[]).includes(reason)) {
      fallbackReasons[reason as CloudReason] += 1;
    }
  }

  const modelMix: Record<string, number> = {};
  for (const row of ai) {
    if (row.model) modelMix[row.model] = (modelMix[row.model] ?? 0) + 1;
  }

  return {
    n: counted.length,
    device_count: device.length,
    cloud_count: cloud.length,
    device_share: counted.length >= minSample ? device.length / counted.length : null,
    cloud_calls_saved: device.length,
    latency_ms: {
      device: latencyCell(
        device.map((row) => row.latency_ms),
        minSample,
      ),
      cloud: latencyCell(
        cloud.map((row) => row.latency_ms),
        minSample,
      ),
    },
    fallback_reasons: fallbackReasons,
    model_mix: modelMix,
    offline_no_threshold: ai.filter((row) => row.fallback_reason === 'offline_no_threshold').length,
    sheet_answers: sheet.length,
  };
}

function langKey(log: PromptLog): LangKey {
  return log.lang === 'es' || log.lang === 'en' ? log.lang : 'unknown';
}

function buildLangCell(rows: PromptLog[], minSample: number): LangCell {
  const counted = rows.filter(isCountedAi);
  const device = counted.filter((row) => row.route === 'device').length;
  const latencies = counted.map((row) => row.latency_ms);
  const enough = counted.length >= minSample;
  return {
    ai_rows: counted.length,
    device_share: enough ? device / counted.length : null,
    latency_p50_ms: enough ? percentile(latencies, 50) : null,
    latency_p95_ms: enough ? percentile(latencies, 95) : null,
    sheet_answers: rows.filter((row) => row.route === 'sheet').length,
  };
}

function buildWindow(rows: PromptLog[], minSample: number): RollupWindow {
  const byFeature = {} as Record<Feature, RollupCell>;
  for (const feature of FEATURES) {
    byFeature[feature] = buildCell(
      rows.filter((row) => row.feature === feature),
      minSample,
    );
  }
  const byLang = {} as Record<LangKey, LangCell>;
  for (const key of ['es', 'en', 'unknown'] as const) {
    byLang[key] = buildLangCell(
      rows.filter((row) => langKey(row) === key),
      minSample,
    );
  }
  return { total: buildCell(rows, minSample), by_feature: byFeature, by_lang: byLang };
}

/** Computes every metric in the analytics spec from real prompt-log rows. Rows from load tests or evals are dropped. */
export function buildRollup(
  logs: PromptLog[],
  now: Date = new Date(),
  minSample: number = confidenceConfig.analytics.min_sample,
): Rollup {
  const live = logs.filter(isLive);
  const since = now.getTime() - DAY_MS;
  const recent = live.filter((row) => {
    const time = Date.parse(row.ts);
    return Number.isFinite(time) && time >= since && time <= now.getTime();
  });
  return {
    generated_at: now.toISOString(),
    source_filter: 'live',
    row_count: live.length,
    min_sample: minSample,
    windows: {
      all: buildWindow(live, minSample),
      last_24h: buildWindow(recent, minSample),
    },
  };
}

export function isRollup(value: unknown): value is Rollup {
  if (!value || typeof value !== 'object') return false;
  const record = value as Partial<Rollup>;
  return (
    typeof record.generated_at === 'string' &&
    typeof record.row_count === 'number' &&
    !!record.windows &&
    !!record.windows.all?.total &&
    !!record.windows.last_24h?.total
  );
}
