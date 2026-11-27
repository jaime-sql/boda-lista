import { mkdirSync } from 'node:fs';
import { expect, test } from '@playwright/test';

mkdirSync('docs/screenshots', { recursive: true });

test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
});

function boxesOverlap(
  a: { x: number; y: number; width: number; height: number },
  b: { x: number; y: number; width: number; height: number },
): boolean {
  return a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
}

test('guest mobile screenshot', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  const heading = page.getByRole('heading', { level: 1 });
  await expect(heading).toContainText('Lucía Mendoza');
  await expect(page.getByText('Hacienda El Sauce')).toBeVisible();

  const calendar = new URL((await page.getByRole('link', { name: 'Al calendario' }).getAttribute('href')) ?? '');
  const [start, end] = (calendar.searchParams.get('dates') ?? '').split('/');
  expect(start).not.toBe(end);
  expect(calendar.searchParams.get('ctz')).toBe('America/El_Salvador');
  expect(calendar.searchParams.get('details') ?? '').toContain('salón');

  await page.getByRole('button', { name: 'EN', exact: true }).click();
  const englishLink = page.getByRole('link', { name: 'Add to calendar' });
  await expect(englishLink).toHaveAttribute('href', /25-minute/);
  await expect(englishLink).toHaveAttribute('href', /ctz=/);
  await page.getByRole('button', { name: 'ES', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Al calendario' })).toHaveAttribute('href', /sal%C3%B3n/);

  const icon = page.locator('.banner-info svg');
  await expect(icon).toHaveAttribute('aria-hidden', 'true');
  const iconBox = await icon.boundingBox();
  expect(iconBox?.width ?? 0).toBeGreaterThanOrEqual(17);
  expect(iconBox?.height ?? 0).toBeGreaterThanOrEqual(17);

  for (const width of [360, 390, 430]) {
    await page.setViewportSize({ width, height: 844 });
    const name = await heading.boundingBox();
    const sprig = await page.locator('.g-hero-art svg').boundingBox();
    expect(name).toBeTruthy();
    expect(sprig).toBeTruthy();
    if (name && sprig) expect(boxesOverlap(name, sprig)).toBe(false);
  }

  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: 'docs/screenshots/guest-mobile.png', fullPage: true });
});

test('guest desktop screenshot', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Lucía Mendoza');
  await page.screenshot({ path: 'docs/screenshots/guest-desktop.png', fullPage: true });
});

test('admin mobile screenshot', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/admin');
  await expect(page.getByRole('heading', { name: 'Diagnóstico' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Entrar con Google' })).toBeVisible();
  await page.screenshot({ path: 'docs/screenshots/admin-mobile.png', fullPage: true });
});

test('admin desktop screenshot', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto('/admin');
  await expect(page.getByRole('heading', { name: 'Diagnóstico' })).toBeVisible();
  await page.screenshot({ path: 'docs/screenshots/admin-desktop.png', fullPage: true });
});

test('guest question reaches an error without Firebase config', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Lucía Mendoza');
  await page.getByLabel('Tu pregunta').fill('¿A qué hora es la ceremonia?');
  await page.getByRole('button', { name: 'Enviar' }).click();
  const alert = page.getByRole('alert');
  await expect(alert).toContainText('No pudimos responder ahora. Intenta de nuevo en un momento.');
  await expect(alert).not.toContainText('Firebase');
  await expect(alert).not.toContainText('VITE_');
  const logged = errors.join('\n');
  expect(logged).toContain('Firebase disabled: missing');
  expect(logged).toContain('VITE_APPCHECK_SITE_KEY');
});

test('quick chip answers from the sheet without Firebase config', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Lucía Mendoza');
  await page.getByRole('button', { name: 'Horario' }).click();
  await expect(page.getByText(/16:00 Ceremonia \/ Ceremony, Jardín Principal/)).toBeVisible();
  await expect(page.getByText('De la ficha de la boda')).toBeVisible();
  await expect(page.getByText('Respuesta poco segura')).toHaveCount(0);
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('offline state is visible on both routes', async ({ page, context }) => {
  await page.goto('/');
  await context.setOffline(true);
  await page.evaluate(() => window.dispatchEvent(new Event('offline')));
  await expect(page.getByText('Sin señal.')).toBeVisible();
  await context.setOffline(false);
  await page.goto('/admin');
  await context.setOffline(true);
  await page.evaluate(() => window.dispatchEvent(new Event('offline')));
  await expect(page.getByText('Sin conexión.')).toBeVisible();
});

test('production build keeps ?debug=1 hidden', async ({ page }) => {
  await page.goto('/?debug=1');
  await expect(page.getByRole('heading', { name: 'Depuración' })).toHaveCount(0);
  await page.goto('/admin?debug=1');
  await expect(page.getByRole('heading', { name: 'Depuración' })).toHaveCount(0);
});
