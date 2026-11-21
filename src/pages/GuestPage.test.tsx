import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { AskResult } from '../ai/types';
import { ToastProvider } from '../components/ToastProvider';
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
});

describe('GuestPage', () => {
  it('shows the sheet, the searching state, and the real route', async () => {
    const user = userEvent.setup();
    const pending = deferred();
    const requestAnswer = vi.fn(() => pending.promise);
    render(
      <ToastProvider>
        <GuestPage requestAnswer={requestAnswer} />
      </ToastProvider>,
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
      <ToastProvider>
        <GuestPage requestAnswer={requestAnswer} />
      </ToastProvider>,
    );
    await screen.findByRole('heading', { level: 1 });
    await user.type(screen.getByLabelText('Tu pregunta'), '¿A qué hora es?');
    await user.click(screen.getByRole('button', { name: 'Enviar' }));
    expect(await screen.findByText(UNSURE_LABEL)).toBeTruthy();
    expect(UNSURE_LABEL).toBe('Respuesta poco segura');
    expect(screen.getByText('En tu teléfono')).toBeTruthy();
  });
});
