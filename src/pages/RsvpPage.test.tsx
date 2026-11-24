import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import type { SavedRsvp } from '../features/rsvp/save';
import * as firebaseConfig from '../firebase/config';
import { RsvpPage, UNSURE_LABEL } from './RsvpPage';

const { extractRsvp, saveRsvp } = vi.hoisted(() => ({
  extractRsvp: vi.fn(),
  saveRsvp: vi.fn<(record: SavedRsvp) => Promise<void>>(async () => undefined),
}));

vi.mock('../features/rsvp/extract', () => ({
  extractRsvp,
}));

vi.mock('../features/rsvp/save', async () => {
  const actual = await vi.importActual<typeof import('../features/rsvp/save')>('../features/rsvp/save');
  return { ...actual, saveRsvp };
});

const extracted = {
  attending: 'yes' as const,
  party_size: 3,
  meal_restrictions: ['vegetarian'],
  kids_count: 1,
  needs_ride: false,
  ambiguous: false,
  confidence: 0.91,
};

afterEach(() => {
  cleanup();
  extractRsvp.mockReset();
  saveRsvp.mockClear();
  vi.restoreAllMocks();
});

function renderRsvp() {
  render(
    <MemoryRouter initialEntries={['/rsvp?code=FAM1']}>
      <RsvpPage />
    </MemoryRouter>,
  );
}

describe('RsvpPage', () => {
  it('confirms extracted fields and saves them', async () => {
    const user = userEvent.setup();
    extractRsvp.mockResolvedValue({
      extraction: extracted,
      result: {
        text: '{}',
        route: 'cloud',
        fallbackReason: 'no_threshold',
        latencyMs: 8,
        inputChars: 20,
        outputChars: 40,
        model: 'gemini-3.5-flash-lite',
      },
      retried: false,
    });
    renderRsvp();
    expect(await screen.findByRole('heading', { name: 'Tu invitación' })).toBeTruthy();
    await user.type(screen.getByLabelText('Respuesta'), 'Si, vamos tres');
    await user.click(screen.getByRole('button', { name: 'Leer respuesta' }));
    expect(await screen.findByRole('button', { name: 'Sí, ahí estaremos' })).toHaveProperty('ariaPressed', 'true');
    await user.click(screen.getByRole('button', { name: 'Enviar respuesta' }));
    expect(await screen.findByRole('heading', { name: 'Gracias por confirmar' })).toBeTruthy();
    expect(saveRsvp).toHaveBeenCalledOnce();
    const saved = saveRsvp.mock.calls[0]?.[0] as SavedRsvp;
    expect(saved.household_id).toBe('FAM1');
    expect(saved.edited).toBe(false);
    expect(saved).not.toHaveProperty('text');
  });

  it('shows an empty form with a revisa note when extraction fails', async () => {
    const user = userEvent.setup();
    extractRsvp.mockResolvedValue({
      extraction: null,
      result: {
        text: 'no',
        route: 'cloud',
        fallbackReason: 'no_threshold',
        latencyMs: 8,
        inputChars: 20,
        outputChars: 2,
        model: 'gemini-3.5-flash-lite',
      },
      retried: true,
    });
    renderRsvp();
    await screen.findByRole('heading', { name: 'Tu invitación' });
    await user.type(screen.getByLabelText('Respuesta'), 'hmm');
    await user.click(screen.getByRole('button', { name: 'Leer respuesta' }));
    expect(await screen.findByText(/Revisa los campos/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Enviar respuesta' })).toHaveProperty('disabled', true);
  });

  it('labels an offline extraction and highlights a maybe reply', async () => {
    const user = userEvent.setup();
    extractRsvp.mockResolvedValue({
      extraction: { ...extracted, attending: 'maybe', ambiguous: true, confidence: 0.2 },
      result: {
        text: '{}',
        route: 'device',
        fallbackReason: 'offline_no_threshold',
        latencyMs: 8,
        inputChars: 20,
        outputChars: 40,
        model: 'gemini-nano',
      },
      retried: false,
    });
    renderRsvp();
    await screen.findByRole('heading', { name: 'Tu invitación' });
    await user.type(screen.getByLabelText('Respuesta'), 'tal vez');
    await user.click(screen.getByRole('button', { name: 'Leer respuesta' }));
    expect(await screen.findByText(UNSURE_LABEL)).toBeTruthy();
    expect(screen.getByText('Revisa estos campos antes de enviar.')).toBeTruthy();
    expect(document.querySelector('.review')).toBeTruthy();
  });

  it('shows a guest-friendly error and logs the missing env name when reading fails', async () => {
    const user = userEvent.setup();
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    vi.spyOn(firebaseConfig, 'missingEnv').mockReturnValue(['VITE_APPCHECK_SITE_KEY']);
    extractRsvp.mockRejectedValue(new Error('firebase-config-missing'));
    renderRsvp();
    await screen.findByRole('heading', { name: 'Tu invitación' });
    await user.type(screen.getByLabelText('Respuesta'), 'Si, vamos tres');
    await user.click(screen.getByRole('button', { name: 'Leer respuesta' }));
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('No pudimos responder ahora. Intenta de nuevo en un momento.');
    expect(alert.textContent).not.toContain('VITE_');
    expect(alert.textContent).not.toContain('variables de entorno');
    expect(screen.queryByText(/Revisa los campos/)).toBeNull();
    expect(errorSpy).toHaveBeenCalledWith('Firebase disabled: missing VITE_APPCHECK_SITE_KEY');

    await user.click(screen.getByRole('button', { name: 'EN' }));
    expect(screen.getByRole('alert').textContent).toContain(
      "We couldn't answer right now. Please try again in a moment.",
    );
  });

  it('keeps the guest on the form when saving fails', async () => {
    const user = userEvent.setup();
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    vi.spyOn(firebaseConfig, 'missingEnv').mockReturnValue(['VITE_APPCHECK_SITE_KEY']);
    extractRsvp.mockResolvedValue({
      extraction: extracted,
      result: {
        text: '{}',
        route: 'cloud',
        fallbackReason: 'no_threshold',
        latencyMs: 8,
        inputChars: 20,
        outputChars: 40,
        model: 'gemini-3.5-flash-lite',
      },
      retried: false,
    });
    saveRsvp.mockRejectedValue(new Error('firebase-config-missing'));
    renderRsvp();
    await screen.findByRole('heading', { name: 'Tu invitación' });
    await user.type(screen.getByLabelText('Respuesta'), 'Si, vamos tres');
    await user.click(screen.getByRole('button', { name: 'Leer respuesta' }));
    await user.click(await screen.findByRole('button', { name: 'Enviar respuesta' }));
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('No pudimos responder ahora. Intenta de nuevo en un momento.');
    expect(screen.queryByRole('heading', { name: 'Gracias por confirmar' })).toBeNull();
    expect(errorSpy).toHaveBeenCalledWith('Firebase disabled: missing VITE_APPCHECK_SITE_KEY');
  });
});
