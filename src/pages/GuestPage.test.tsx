import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import type { AskResult } from '../ai/types';
import { ToastProvider } from '../components/ToastProvider';
import * as firebaseConfig from '../firebase/config';
import { GuestPage, UNSURE_LABEL } from './GuestPage';

function deferred() {
  let resolve: (value: AskResult) => void = () => undefined;
  const promise = new Promise<AskResult>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('GuestPage', () => {
  it('shows the sheet, the searching state, and the real route', async () => {
    const user = userEvent.setup();
    const pending = deferred();
    const requestAnswer = vi.fn(() => pending.promise);
    render(
      <MemoryRouter>
        <ToastProvider>
          <GuestPage requestAnswer={requestAnswer} />
        </ToastProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { level: 1 })).toHaveProperty(
      'textContent',
      expect.stringContaining('Lucía Mendoza'),
    );
    expect(screen.getByText(/Hacienda El Sauce/)).toBeTruthy();
    expect(screen.queryByText(/Jardín El Ejemplo/)).toBeNull();
    await user.type(screen.getByLabelText('Tu pregunta'), '¿A qué hora es la ceremonia?');
    await user.click(screen.getByRole('button', { name: 'Enviar' }));
    expect(await screen.findByText('Buscando en la información de la boda…')).toBeTruthy();

    pending.resolve({
      text: 'La ceremonia es a las 16:00.',
      route: 'cloud',
      fallbackReason: 'no_model',
      latencyMs: 10,
      inputChars: 20,
      outputChars: 28,
      model: 'gemini-3.5-flash-lite',
    });

    expect(await screen.findByText('En la nube')).toBeTruthy();
    expect(screen.getByText('La ceremonia es a las 16:00.')).toBeTruthy();
    expect(screen.queryByText(UNSURE_LABEL)).toBeNull();
  });

  it('labels an offline answer with no threshold', async () => {
    const user = userEvent.setup();
    const requestAnswer = vi.fn(async () => ({
      text: 'La ceremonia es a las 16:00.',
      route: 'device' as const,
      fallbackReason: 'offline_no_threshold' as const,
      latencyMs: 4,
      inputChars: 12,
      outputChars: 28,
      model: 'gemini-nano',
    }));
    render(
      <MemoryRouter>
        <ToastProvider>
          <GuestPage requestAnswer={requestAnswer} />
        </ToastProvider>
      </MemoryRouter>,
    );
    await screen.findByRole('heading', { level: 1 });
    await user.type(screen.getByLabelText('Tu pregunta'), '¿A qué hora es?');
    await user.click(screen.getByRole('button', { name: 'Enviar' }));
    expect(await screen.findByText(UNSURE_LABEL)).toBeTruthy();
    expect(UNSURE_LABEL).toBe('Respuesta poco segura');
    expect(screen.getByText('En tu teléfono')).toBeTruthy();
  });

  it('shows a guest-friendly error and logs the missing env name', async () => {
    const user = userEvent.setup();
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    vi.spyOn(firebaseConfig, 'missingEnv').mockReturnValue(['VITE_APPCHECK_SITE_KEY']);
    const requestAnswer = vi.fn(async () => {
      throw new Error('firebase-config-missing');
    });
    render(
      <MemoryRouter>
        <ToastProvider>
          <GuestPage requestAnswer={requestAnswer} />
        </ToastProvider>
      </MemoryRouter>,
    );
    await screen.findByRole('heading', { level: 1 });
    await user.type(screen.getByLabelText('Tu pregunta'), '¿A qué hora es la ceremonia?');
    await user.click(screen.getByRole('button', { name: 'Enviar' }));
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('No pudimos responder ahora. Intenta de nuevo en un momento.');
    expect(alert.textContent).not.toContain('VITE_');
    expect(alert.textContent).not.toContain('Firebase');
    expect(alert.textContent).not.toContain('variables de entorno');
    expect(errorSpy).toHaveBeenCalledWith('Firebase disabled: missing VITE_APPCHECK_SITE_KEY');

    await user.click(screen.getByRole('button', { name: 'EN' }));
    expect(screen.getByRole('alert').textContent).toContain(
      "We couldn't answer right now. Please try again in a moment.",
    );
  });
});
