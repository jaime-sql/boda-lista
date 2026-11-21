import { mkdirSync } from 'node:fs';
import { expect, test } from '@playwright/test';

mkdirSync('docs/screenshots', { recursive: true });

test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
});

test('guest mobile screenshot', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Preguntas de la boda' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Todavía no hay una respuesta' })).toBeVisible();
  await page.screenshot({ path: 'docs/screenshots/guest-mobile.png', fullPage: true });
});

test('guest desktop screenshot', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Preguntas de la boda' })).toBeVisible();
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
  await page.goto('/');
  await page.getByRole('button', { name: 'Qué cubre la hoja' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('button', { name: 'Cerrar' }).click();
  await expect(page.getByRole('dialog')).toBeHidden();

  await page.getByRole('button', { name: 'Preguntar' }).click();
  await expect(page.getByText('Escribe una pregunta.')).toBeVisible();

  await page.getByLabel('Tu pregunta').fill('¿A qué hora es la ceremonia?');
  await page.getByRole('button', { name: 'Preguntar' }).click();
  await expect(page.getByRole('alert')).toContainText('Firebase');
});

test('offline state is visible on both routes', async ({ page, context }) => {
  await page.goto('/');
  await context.setOffline(true);
  await page.evaluate(() => window.dispatchEvent(new Event('offline')));
  await expect(page.getByRole('heading', { name: 'Sin conexión' })).toBeVisible();
  await page.getByRole('link', { name: 'Diagnóstico' }).click();
  await expect(page.getByRole('heading', { name: 'Diagnóstico' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Sin conexión' })).toBeVisible();
});

test('production build keeps ?debug=1 hidden', async ({ page }) => {
  await page.goto('/?debug=1');
  await expect(page.getByRole('heading', { name: 'Depuración' })).toHaveCount(0);
  await page.goto('/admin?debug=1');
  await expect(page.getByRole('heading', { name: 'Depuración' })).toHaveCount(0);
});
