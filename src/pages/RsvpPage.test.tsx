import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import type { SavedRsvp } from '../features/rsvp/save';
import type { SavedSong } from '../features/song/save';
import * as firebaseConfig from '../firebase/config';
import { RsvpPage, UNSURE_LABEL } from './RsvpPage';

const { extractRsvp, saveRsvp, extractSong, saveSong } = vi.hoisted(() => ({
  extractRsvp: vi.fn(),
  saveRsvp: vi.fn<(record: SavedRsvp) => Promise<void>>(async () => undefined),
  extractSong: vi.fn(),
  saveSong: vi.fn<(record: SavedSong) => Promise<void>>(async () => undefined),
}));

vi.mock('../features/rsvp/extract', () => ({
  extractRsvp,
}));

vi.mock('../features/rsvp/save', async () => {
  const actual = await vi.importActual<typeof import('../features/rsvp/save')>('../features/rsvp/save');
  return { ...actual, saveRsvp };
});

vi.mock('../features/song/extract', () => ({
  extractSong,
}));

vi.mock('../features/song/save', async () => {
  const actual = await vi.importActual<typeof import('../features/song/save')>('../features/song/save');
  return { ...actual, saveSong };
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
  extractSong.mockReset();
  saveSong.mockClear();
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
  it('confirms extracted fields, saves requested songs preserving slots, and shows summary', async () => {
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
    extractSong
      .mockResolvedValueOnce({
        extraction: {
          title: 'Vivir Mi Vida',
          artist: 'Marc Anthony',
          energy: 'dance',
          ambiguous: false,
          confidence: 0.94,
        },
        result: {
          text: '{}',
          route: 'device',
          fallbackReason: null,
          latencyMs: 6,
          inputChars: 18,
          outputChars: 30,
          model: 'gemini-nano',
        },
        retried: false,
      })
      .mockResolvedValueOnce({
        extraction: {
          title: null,
          artist: 'Marc Anthony',
          energy: 'dance',
          ambiguous: true,
          confidence: 0.4,
        },
        result: {
          text: '{}',
          route: 'cloud',
          fallbackReason: 'low_confidence',
          latencyMs: 9,
          inputChars: 18,
          outputChars: 30,
          model: 'gemini-3.5-flash-lite',
        },
        retried: false,
      });

    renderRsvp();
    expect(await screen.findByRole('heading', { name: 'Tu invitación' })).toBeTruthy();
    await user.type(screen.getByLabelText('Respuesta'), 'Si, vamos tres');
    await user.click(screen.getByRole('button', { name: 'Leer respuesta' }));
    expect(await screen.findByRole('button', { name: 'Sí, ahí estaremos' })).toHaveProperty('ariaPressed', 'true');
    await user.click(screen.getByRole('button', { name: 'Continuar' }));

    expect(await screen.findByRole('heading', { name: 'Canciones para el DJ' })).toBeTruthy();
    expect(saveRsvp).toHaveBeenCalledOnce();
    const saved = saveRsvp.mock.calls[0]?.[0] as SavedRsvp;
    expect(saved.household_id).toBe('FAM1');
    expect(saved.edited).toBe(false);
    expect(saved).not.toHaveProperty('text');

    await user.type(screen.getByLabelText('Canción 1'), 'Vivir mi vida de Marc Anthony');
    await user.type(screen.getByLabelText('Canción 3'), 'la de Marc Anthony');
    await user.click(screen.getByRole('button', { name: 'Enviar respuesta' }));

    expect(await screen.findByRole('heading', { name: 'Gracias por confirmar' })).toBeTruthy();
    expect(saveSong).toHaveBeenCalledTimes(2);
    expect(saveSong.mock.calls[0]?.[0]).toMatchObject({
      household_id: 'FAM1',
      slot: 1,
      title: 'Vivir Mi Vida',
      artist: 'Marc Anthony',
      energy: 'dance',
      ambiguous: false,
    });
    expect(saveSong.mock.calls[1]?.[0]).toMatchObject({
      household_id: 'FAM1',
      slot: 3,
      title: null,
      artist: 'Marc Anthony',
      ambiguous: true,
      raw_text: 'la de Marc Anthony',
    });
    expect(screen.getByText('Vivir Mi Vida · Marc Anthony')).toBeTruthy();
    expect(screen.getByText('“la de Marc Anthony” (Revisar)')).toBeTruthy();
    expect(screen.getByText('En tu teléfono')).toBeTruthy();
    expect(screen.getByText('En la nube')).toBeTruthy();
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
    expect(screen.getByRole('button', { name: 'Continuar' })).toHaveProperty('disabled', true);
  });

  it('labels an offline extraction, highlights a maybe reply, and allows skipping songs', async () => {
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

    await user.click(screen.getByRole('button', { name: 'Continuar' }));
    expect(await screen.findByRole('heading', { name: 'Canciones para el DJ' })).toBeTruthy();
    await user.click(screen.getByRole('button', { name: 'Omitir canciones' }));
    expect(await screen.findByRole('heading', { name: 'Gracias por confirmar' })).toBeTruthy();
    expect(saveSong).not.toHaveBeenCalled();
    expect(screen.getByText('Sin canciones')).toBeTruthy();
  });

  it('skips songs step directly when guest is not attending', async () => {
    const user = userEvent.setup();
    extractRsvp.mockResolvedValue({
      extraction: { ...extracted, attending: 'no', party_size: null, kids_count: null },
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
    await screen.findByRole('heading', { name: 'Tu invitación' });
    await user.type(screen.getByLabelText('Respuesta'), 'No podremos ir');
    await user.click(screen.getByRole('button', { name: 'Leer respuesta' }));
    await user.click(await screen.findByRole('button', { name: 'Enviar respuesta' }));
    expect(await screen.findByRole('heading', { name: 'Gracias por confirmar' })).toBeTruthy();
    expect(screen.queryByRole('heading', { name: 'Canciones para el DJ' })).toBeNull();
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
    await user.click(await screen.findByRole('button', { name: 'Continuar' }));
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('No pudimos responder ahora. Intenta de nuevo en un momento.');
    expect(screen.queryByRole('heading', { name: 'Gracias por confirmar' })).toBeNull();
    expect(errorSpy).toHaveBeenCalledWith('Firebase disabled: missing VITE_APPCHECK_SITE_KEY');
  });
});
