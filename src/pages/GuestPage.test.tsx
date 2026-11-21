import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import type { AskResult } from '../ai/types';
import { THINKING_LABEL } from '../components/ScreenState';
import { ToastProvider } from '../components/ToastProvider';
import { GuestPage } from './GuestPage';

function deferred() {
  let resolve: (value: AskResult) => void = () => undefined;
  const promise = new Promise<AskResult>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

describe('GuestPage', () => {
  it('shows the thinking state and the badge for the real route', async () => {
    const user = userEvent.setup();
    const pending = deferred();
    const requestAnswer = vi.fn(() => pending.promise);
    render(
      <ToastProvider>
        <GuestPage requestAnswer={requestAnswer} />
      </ToastProvider>,
    );

    expect(await screen.findByRole('heading', { name: 'Todavía no hay una respuesta' })).toBeTruthy();
    await user.type(screen.getByLabelText('Tu pregunta'), '¿A qué hora es la ceremonia?');
    await user.click(screen.getByRole('button', { name: 'Preguntar' }));
    expect(await screen.findByText(THINKING_LABEL)).toBeTruthy();
    expect(THINKING_LABEL).toBe('pensando en tu teléfono...');

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
    expect(screen.queryByText('En tu teléfono')).toBeNull();
    expect(screen.getByText('La ceremonia es a las 16:00.')).toBeTruthy();
  });
});
