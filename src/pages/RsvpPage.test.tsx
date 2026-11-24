import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import type { SavedRsvp } from '../features/rsvp/save';
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
    expect(
      screen.getByText(
        'Escribe tu respuesta como se la mandarías a los novios: quiénes van y si alguien tiene alguna restricción.',
      ),
    ).toBeTruthy();
    expect(screen.getByLabelText('Código de invitación')).toHaveProperty('placeholder', 'Ej. GARCIA-24');
    await user.click(screen.getByRole('button', { name: /^EN$/ }));
    expect(
      screen.getByText("Write your reply like you'd text the couple: who's coming and any dietary needs."),
    ).toBeTruthy();
    expect(screen.getByLabelText('Invite code')).toHaveProperty('placeholder', 'e.g. GARCIA-24');
    await user.click(screen.getByRole('button', { name: /^ES$/ }));
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
});
