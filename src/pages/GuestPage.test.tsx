import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import * as hybrid from '../ai/hybrid';
import type { AskContext, AskResult } from '../ai/types';
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
    const requestAnswer = vi.fn((_prompt: string, _context: AskContext) => pending.promise);
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
    const userTurn = String(requestAnswer.mock.calls[0]?.[0]);
    expect(userTurn).toContain('lang: es');
    expect(userTurn).toContain('Idioma de respuesta: español');
    expect(requestAnswer.mock.calls[0]?.[1]).toMatchObject({ feature: 'guest_question', lang: 'es' });
  });

  it('marks an English question with lang en even when the page is Spanish and the question names a place', async () => {
    const user = userEvent.setup();
    const requestAnswer = vi.fn(async (_prompt: string, _context: AskContext) => ({
      text: 'The ceremony is at 16:00.',
      route: 'cloud' as const,
      fallbackReason: 'no_threshold' as const,
      latencyMs: 8,
      inputChars: 40,
      outputChars: 28,
      model: 'gemini-3.5-flash-lite',
    }));
    render(
      <MemoryRouter>
        <ToastProvider>
          <GuestPage requestAnswer={requestAnswer} />
        </ToastProvider>
      </MemoryRouter>,
    );
    await screen.findByRole('heading', { level: 1 });
    await user.type(screen.getByLabelText('Tu pregunta'), 'What time is the ceremony at Salón El Encanto?');
    await user.click(screen.getByRole('button', { name: 'Enviar' }));
    const userTurn = String(requestAnswer.mock.calls[0]?.[0]);
    expect(userTurn).toContain('lang: en');
    expect(userTurn).toContain('Answer language: English');
    expect(userTurn).toContain('Salón El Encanto');
    expect(requestAnswer.mock.calls[0]?.[1]).toMatchObject({ lang: 'en' });
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

  it('answers every quick chip from the sheet and never calls the model client', async () => {
    const user = userEvent.setup();
    const requestAnswer = vi.fn();
    const ask = vi.spyOn(hybrid, 'ask');
    render(
      <MemoryRouter>
        <ToastProvider>
          <GuestPage requestAnswer={requestAnswer} />
        </ToastProvider>
      </MemoryRouter>,
    );
    await screen.findByRole('heading', { level: 1 });
    for (const label of ['Horario', 'Lugar', 'Vestimenta', 'Parqueo', 'Regalos', 'Contactos']) {
      await user.click(screen.getByRole('button', { name: label }));
    }
    await user.click(screen.getByRole('button', { name: 'EN' }));
    for (const label of ['Schedule', 'Venue', 'Dress code', 'Parking', 'Gifts', 'Contacts']) {
      await user.click(screen.getByRole('button', { name: label }));
    }

    expect(requestAnswer).not.toHaveBeenCalled();
    expect(ask).not.toHaveBeenCalled();
    expect(screen.queryByText('Buscando en la información de la boda…')).toBeNull();
    expect(screen.queryByText(/Firebase/)).toBeNull();
    expect(screen.getAllByText('En la hoja').length).toBe(12);
    expect(screen.queryByText('En la nube')).toBeNull();
    expect(screen.queryByText('En tu teléfono')).toBeNull();
    expect(screen.getAllByText(/16:00 Ceremonia \/ Ceremony, Jardín Principal/)).toHaveLength(2);
    expect(screen.getByText(/The wedding is at Hacienda El Sauce, Km 12.5 Carretera a La Libertad/)).toBeTruthy();
    expect(screen.getByText(/Cocktail attire. Guayaberas are welcome./)).toBeTruthy();
    expect(screen.getByText(/Do not park on the highway shoulder./)).toBeTruthy();
    expect(screen.getByText(/Money envelopes are preferred./)).toBeTruthy();
    expect(screen.getByText(/Contacts: Elena Castro/)).toBeTruthy();
  });
});
