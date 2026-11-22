import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppShell } from '../components/AppShell';
import { ToastProvider } from '../components/ToastProvider';
import { clearLastPromptLog, rememberPromptLog } from './sessionLog';

vi.mock('../ai/device', () => ({
  probeDeviceModel: vi.fn(async () => 'downloadable'),
}));

vi.mock('../firebase/client', () => ({
  appCheckTokenPresence: vi.fn(async () => 'no'),
}));

const SECRET = 'SECRET_PROMPT_DO_NOT_SHOW';

describe('DebugPanel', () => {
  beforeEach(() => {
    clearLastPromptLog();
  });

  it('hides the panel on a production build', () => {
    render(
      <MemoryRouter initialEntries={['/?debug=1']}>
        <ToastProvider>
          <AppShell debugEnv={{ DEV: false }}>
            <p>Inicio</p>
          </AppShell>
        </ToastProvider>
      </MemoryRouter>,
    );
    expect(screen.queryByRole('heading', { name: 'Depuración' })).toBeNull();
  });

  it('shows availability, presence, and the local log on a preview build', async () => {
    rememberPromptLog('doc-9', {
      ts: '2026-11-21T18:00:00.000Z',
      feature: 'guest_question',
      route: 'device',
      fallback_reason: 'no_threshold',
      latency_ms: 15,
      input_chars: 120,
      output_chars: 30,
      model: 'gemini-nano',
      confidence: 0.9,
      session_id: 'session-xyz123',
    });
    sessionStorage.setItem(
      'boda-lista.note',
      JSON.stringify({ prompt: SECRET, guest: 'Nombre Falso' }),
    );

    render(
      <MemoryRouter initialEntries={['/?debug=1']}>
        <ToastProvider>
          <AppShell debugEnv={{ DEV: false, VITE_ENABLE_DEBUG: 'true' }}>
            <p>Inicio</p>
          </AppShell>
        </ToastProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: 'Depuración' })).toBeTruthy();
    expect(await screen.findByText(/downloadable/)).toBeTruthy();
    expect(screen.getByText('En tu teléfono')).toBeTruthy();
    expect(screen.getByText('no')).toBeTruthy();
    expect(screen.getByText('doc-9')).toBeTruthy();
    expect(screen.getByText('gemini-nano')).toBeTruthy();
    expect(screen.getByText('session-xyz123')).toBeTruthy();
    expect(screen.getByText('no_threshold')).toBeTruthy();
    expect(document.body.textContent).not.toContain(SECRET);
    expect(document.body.textContent).not.toContain('Nombre Falso');
  });
});
