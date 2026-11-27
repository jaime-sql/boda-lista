import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { PromptLog, Route } from '../../ai/types';
import { AnalyticsPanel, FEW_DATA, formatLatency, formatPercent } from './AnalyticsPanel';
import { buildRollup } from './rollup';

const { fetchAllLogs } = vi.hoisted(() => ({ fetchAllLogs: vi.fn<() => Promise<PromptLog[]>>() }));

vi.mock('../../firebase/logs', () => ({ fetchAllLogs }));

const NOW = new Date();

function logs(count: number, over: Partial<PromptLog> & { route: Route }): PromptLog[] {
  return Array.from({ length: count }, (_, index) => ({
    ts: new Date(NOW.getTime() - 60_000).toISOString(),
    feature: 'guest_question' as const,
    fallback_reason: null,
    latency_ms: 400,
    input_chars: 10,
    output_chars: 20,
    model: over.route === 'sheet' ? null : 'model-x',
    confidence: null,
    session_id: `session-${over.route}-${index}`,
    ...over,
  }));
}

function renderPanel(props: Partial<React.ComponentProps<typeof AnalyticsPanel>> = {}) {
  return render(<AnalyticsPanel signedIn online reload={0} onRetry={() => undefined} {...props} />);
}

function stubSnapshot(body: unknown | null) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () =>
      body === null
        ? new Response('<html></html>', { status: 200, headers: { 'content-type': 'text/html' } })
        : new Response(JSON.stringify(body), { status: 200, headers: { 'content-type': 'application/json' } }),
    ),
  );
}

afterEach(() => {
  cleanup();
  fetchAllLogs.mockReset();
  vi.unstubAllGlobals();
});

describe('formatters', () => {
  it('formats percentages and latency', () => {
    expect(formatPercent(0.666)).toBe('67\u00a0%');
    expect(formatLatency(420)).toBe('420 ms');
    expect(formatLatency(1250)).toBe('1.3 s');
  });
});

describe('AnalyticsPanel', () => {
  it('shows tiles, per-feature bars and cloud reasons computed from the log', async () => {
    fetchAllLogs.mockResolvedValue([
      ...logs(30, { route: 'device', latency_ms: 300 }),
      ...logs(10, { route: 'cloud', fallback_reason: 'no_model', latency_ms: 1500 }),
      ...logs(20, { route: 'cloud', fallback_reason: 'long_input', latency_ms: 1500, feature: 'rsvp' }),
      ...logs(6, { route: 'sheet' }),
      ...logs(3, { route: 'device', fallback_reason: 'offline_no_threshold' }),
    ]);
    renderPanel();
    expect(await screen.findByRole('heading', { name: 'Cómo responde la IA' })).toBeTruthy();
    await screen.findByText('50 %');
    expect(screen.getByText('de 60 respuestas con IA')).toBeTruthy();
    expect(screen.getByText('Llamadas a la nube ahorradas').nextElementSibling?.textContent).toBe('30');
    expect(screen.getByText('300 ms')).toBeTruthy();
    expect(screen.getByText('1.5 s')).toBeTruthy();
    expect(screen.getByText(/Respondido desde la ficha: 6/)).toBeTruthy();
    expect(screen.getAllByText('Sin umbral aún')).toHaveLength(3);
    expect(screen.getByText('Sin conexión, sin umbral')).toBeTruthy();
    expect(screen.getByText('No había modelo en el teléfono')).toBeTruthy();
    expect(screen.getByText('El texto era muy largo')).toBeTruthy();
    expect(screen.getByRole('button', { name: /Descargar rollup.json/ })).toBeTruthy();
    expect(screen.queryByText('Confianza baja, bajo el umbral de cada función')).toBeNull();
  });

  it('shows the few-data text instead of a percentage under the minimum sample', async () => {
    fetchAllLogs.mockResolvedValue(logs(5, { route: 'device' }));
    renderPanel();
    expect(await screen.findByText('5 de 20 respuestas')).toBeTruthy();
    expect(screen.getAllByText(FEW_DATA).length).toBeGreaterThan(0);
    expect(screen.queryByText(/\d+ %/)).toBeNull();
  });

  it('switches to the last 24 hours window', async () => {
    const user = userEvent.setup();
    fetchAllLogs.mockResolvedValue([
      ...logs(25, { route: 'device' }),
      ...logs(25, {
        route: 'cloud',
        fallback_reason: 'no_model',
        ts: new Date(NOW.getTime() - 3 * 24 * 3600 * 1000).toISOString(),
      }),
    ]);
    renderPanel();
    await screen.findByText('50 %');
    await user.click(screen.getByRole('button', { name: 'Últimas 24 h' }));
    expect(await screen.findByText('100 %')).toBeTruthy();
  });

  it('shows the empty state when the log has no rows', async () => {
    fetchAllLogs.mockResolvedValue([]);
    renderPanel();
    expect(await screen.findByText('Aún no hay preguntas')).toBeTruthy();
  });

  it('falls back to the saved copy when the live read fails', async () => {
    fetchAllLogs.mockRejectedValue(new Error('denied'));
    stubSnapshot(buildRollup(logs(40, { route: 'device' }), new Date('2026-11-29T17:00:00.000Z')));
    renderPanel();
    expect(await screen.findByText(/Mostramos la última copia guardada/)).toBeTruthy();
    expect(screen.getByText('100 %')).toBeTruthy();
    expect(screen.getByText(/Copia guardada del/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Descargar rollup.json/ })).toBeNull();
  });

  it('shows an error with retry when the live read fails and no copy exists', async () => {
    const onRetry = vi.fn();
    const user = userEvent.setup();
    fetchAllLogs.mockRejectedValue(new Error('denied'));
    stubSnapshot(null);
    renderPanel({ onRetry });
    await user.click(await screen.findByRole('button', { name: 'Reintentar' }));
    expect(onRetry).toHaveBeenCalled();
  });

  it('uses the saved copy without signing in and renders nothing when there is none', async () => {
    stubSnapshot(buildRollup(logs(40, { route: 'device' }), NOW));
    const first = renderPanel({ signedIn: false });
    expect(await screen.findByText('100 %')).toBeTruthy();
    expect(fetchAllLogs).not.toHaveBeenCalled();
    first.unmount();

    stubSnapshot(null);
    const second = renderPanel({ signedIn: false });
    await waitFor(() => expect(second.container.querySelector('section')).toBeNull());
  });

  it('renders nothing when offline with no saved copy, since the page already says it is offline', async () => {
    stubSnapshot(null);
    const view = renderPanel({ online: false });
    await waitFor(() => expect(view.container.querySelector('section')).toBeNull());
    expect(fetchAllLogs).not.toHaveBeenCalled();
  });

  it('shows the saved copy when offline', async () => {
    stubSnapshot(buildRollup(logs(40, { route: 'device' }), NOW));
    renderPanel({ online: false });
    expect(await screen.findByText('100 %')).toBeTruthy();
    expect(screen.getByText(/Copia guardada del/)).toBeTruthy();
  });
});
