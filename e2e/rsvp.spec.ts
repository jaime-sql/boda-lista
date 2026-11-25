import { expect, test } from '@playwright/test';

const onlineFields = {
  attending: 'yes',
  party_size: 3,
  meal_restrictions: ['vegetarian'],
  kids_count: 1,
  needs_ride: false,
  ambiguous: false,
  confidence: 0.9,
};

const offlineFields = {
  ...onlineFields,
  attending: 'maybe',
  ambiguous: true,
  confidence: 0.3,
};

const songClear = {
  title: 'Vivir Mi Vida',
  artist: 'Marc Anthony',
  energy: 'dance',
  ambiguous: false,
  confidence: 0.94,
};

const songAmbiguous = {
  title: null,
  artist: 'Marc Anthony',
  energy: 'dance',
  ambiguous: true,
  confidence: 0.42,
};

function result(text: string, route: 'cloud' | 'device', fallbackReason: string) {
  return {
    text,
    route,
    fallbackReason,
    latencyMs: 12,
    inputChars: 24,
    outputChars: text.length,
    model: route === 'cloud' ? 'gemini-3.5-flash-lite' : 'gemini-nano',
  };
}

test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.addInitScript(
    ({ online, offline, songOnline, songOffline, songAmb }) => {
      sessionStorage.setItem('boda-lista.rsvp-mock', JSON.stringify({ online, offline }));
      sessionStorage.setItem(
        'boda-lista.song-mock',
        JSON.stringify({
          online: songOnline,
          offline: songOffline,
          byText: {
            'la de Marc Anthony': { online: songAmb, offline: songAmb },
          },
        }),
      );
    },
    {
      online: result(JSON.stringify(onlineFields), 'cloud', 'no_threshold'),
      offline: result(JSON.stringify(offlineFields), 'device', 'offline_no_threshold'),
      songOnline: result(JSON.stringify(songClear), 'cloud', 'no_threshold'),
      songOffline: result(JSON.stringify(songClear), 'device', 'offline_no_threshold'),
      songAmb: result(JSON.stringify(songAmbiguous), 'cloud', 'no_threshold'),
    },
  );
});

test('online reply confirms, adds songs, and reaches success', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/rsvp?code=FAM1');
  await expect(page.getByRole('heading', { name: 'Tu invitación' })).toBeVisible();
  await page.screenshot({ path: 'docs/screenshots/rsvp-paste-mobile.png', fullPage: true });
  await page.getByLabel('Respuesta').fill('Si, vamos tres. Uno vegetariano.');
  await page.getByRole('button', { name: 'Leer respuesta' }).click();
  await expect(page.getByRole('button', { name: 'Sí, ahí estaremos' })).toHaveAttribute('aria-pressed', 'true');
  await page.screenshot({ path: 'docs/screenshots/rsvp-confirm-mobile.png', fullPage: true });
  await page.getByRole('button', { name: 'Continuar' }).click();

  await expect(page.getByRole('heading', { name: 'Canciones para el DJ' })).toBeVisible();
  await page.getByLabel('Canción 1').fill('Vivir mi vida de Marc Anthony');
  await page.getByLabel('Canción 3').fill('la de Marc Anthony');
  await page.screenshot({ path: 'docs/screenshots/rsvp-songs-mobile.png', fullPage: true });
  await page.getByRole('button', { name: 'Enviar respuesta' }).click();

  await expect(page.getByRole('heading', { name: 'Gracias por confirmar' })).toBeVisible();
  await expect(page.getByText('Hacienda El Sauce')).toBeVisible();
  await expect(page.getByText('Vivir Mi Vida · Marc Anthony')).toBeVisible();
  await expect(page.getByText('“la de Marc Anthony” (Revisar)')).toBeVisible();
  await page.screenshot({ path: 'docs/screenshots/rsvp-success-mobile.png', fullPage: true });
});

test('online reply can skip songs to reach success', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/rsvp?code=FAM1');
  await page.getByLabel('Respuesta').fill('Si, vamos tres. Uno vegetariano.');
  await page.getByRole('button', { name: 'Leer respuesta' }).click();
  await page.getByRole('button', { name: 'Continuar' }).click();
  await expect(page.getByRole('heading', { name: 'Canciones para el DJ' })).toBeVisible();
  await page.getByRole('button', { name: 'Omitir canciones' }).click();
  await expect(page.getByRole('heading', { name: 'Gracias por confirmar' })).toBeVisible();
  await expect(page.getByText('Sin canciones')).toBeVisible();
});

test('offline reply uses the unsure label before success', async ({ page, context }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto('/rsvp?code=FAM1');
  await context.setOffline(true);
  await page.evaluate(() => window.dispatchEvent(new Event('offline')));
  await page.getByLabel('Respuesta').fill('Tal vez vamos.');
  await page.getByRole('button', { name: 'Leer respuesta' }).click();
  await expect(page.getByText('Respuesta poco segura')).toBeVisible();
  await expect(page.getByText('Revisa estos campos antes de enviar.')).toBeVisible();
  await page.screenshot({ path: 'docs/screenshots/rsvp-offline-desktop.png', fullPage: true });
  await page.getByRole('button', { name: 'Continuar' }).click();
  await expect(page.getByRole('heading', { name: 'Canciones para el DJ' })).toBeVisible();
  await page.getByLabel('Canción 1').fill('Vivir mi vida de Marc Anthony');
  await page.getByRole('button', { name: 'Enviar respuesta' }).click();
  await expect(page.getByRole('heading', { name: 'Gracias por confirmar' })).toBeVisible();
  await expect(page.getByText('En tu teléfono')).toBeVisible();
});

test('declined reply skips the songs step directly to success', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/rsvp?code=FAM1');
  await page.getByLabel('Respuesta').fill('No podemos ir.');
  await page.getByRole('button', { name: 'Leer respuesta' }).click();
  await page.getByRole('button', { name: 'No podremos ir' }).click();
  await page.getByRole('button', { name: 'Enviar respuesta' }).click();
  await expect(page.getByRole('heading', { name: 'Gracias por confirmar' })).toBeVisible();
  await expect(page.getByText('Canciones')).toHaveCount(0);
});
