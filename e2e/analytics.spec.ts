import { expect, test } from '@playwright/test';
import type { LangCell, Rollup, RollupCell, RollupWindow } from '../src/features/analytics/rollup';

const NOW = new Date();

function cell(over: Partial<RollupCell>): RollupCell {
  return {
    n: 0,
    device_count: 0,
    cloud_count: 0,
    device_share: null,
    cloud_calls_saved: 0,
    latency_ms: { device: { p50: null, p95: null, n: 0 }, cloud: { p50: null, p95: null, n: 0 } },
    fallback_reasons: { no_model: 0, low_confidence: 0, long_input: 0, no_threshold: 0 },
    model_mix: {},
    offline_no_threshold: 0,
    sheet_answers: 0,
    ...over,
  };
}

const langCell: LangCell = { ai_rows: 0, device_share: null, latency_p50_ms: null, latency_p95_ms: null, sheet_answers: 0 };

const total = cell({
  n: 52,
  device_count: 30,
  cloud_count: 22,
  device_share: 30 / 52,
  cloud_calls_saved: 30,
  latency_ms: {
    device: { p50: 350, p95: 600, n: 30 },
    cloud: { p50: 1700, p95: 2400, n: 22 },
  },
  fallback_reasons: { no_model: 12, low_confidence: 0, long_input: 10, no_threshold: 0 },
  model_mix: { 'model-x': 52 },
  offline_no_threshold: 4,
  sheet_answers: 8,
});

const window_: RollupWindow = {
  total,
  by_feature: {
    guest_question: cell({ n: 42, device_count: 30, cloud_count: 12, device_share: 30 / 42, cloud_calls_saved: 30, offline_no_threshold: 4 }),
    rsvp: cell({ n: 10, device_count: 0, cloud_count: 10, device_share: null }),
    song: cell({}),
  },
  by_lang: { es: langCell, en: langCell, unknown: langCell },
};

const rollup: Rollup = {
  generated_at: NOW.toISOString(),
  source_filter: 'live',
  row_count: 64,
  min_sample: 20,
  windows: { all: window_, last_24h: window_ },
};

test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
});

test('analytics panel shows the saved copy on a phone without horizontal overflow', async ({ page }) => {
  await page.route('**/analytics/rollup.json', (route) => route.fulfill({ json: rollup }));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/admin');

  await expect(page.getByRole('heading', { name: 'Cómo responde la IA' })).toBeVisible();
  await expect(page.getByText('Respondido en tu teléfono')).toBeVisible();
  await expect(page.getByText('Llamadas a la nube ahorradas')).toBeVisible();
  await expect(page.getByText('Sin conexión, sin umbral')).toBeVisible();
  await expect(page.getByText(/Copia guardada del/)).toBeVisible();

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);

  const chip = await page.getByRole('button', { name: 'Últimas 24 h' }).boundingBox();
  expect(chip?.height ?? 0).toBeGreaterThanOrEqual(48);

  await page.screenshot({ path: 'docs/screenshots/analytics-mobile.png', fullPage: true });
});

test('admin hides the analytics panel when there is no saved copy and no sign-in', async ({ page }) => {
  await page.goto('/admin');
  await expect(page.getByRole('heading', { name: 'Diagnóstico' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Cómo responde la IA' })).toHaveCount(0);
});
