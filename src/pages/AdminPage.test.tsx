import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ToastProvider } from '../components/ToastProvider';
import type { SavedSong } from '../features/song/save';
import { AdminPage } from './AdminPage';

const { fetchSongs, fetchRecentLogs, fetchAllLogs } = vi.hoisted(() => ({
  fetchSongs: vi.fn<() => Promise<SavedSong[]>>(),
  fetchRecentLogs: vi.fn(async () => []),
  fetchAllLogs: vi.fn(async () => []),
}));

vi.mock('firebase/auth', () => ({
  GoogleAuthProvider: class GoogleAuthProvider {},
  onAuthStateChanged: (_auth: unknown, cb: (user: { uid: string } | null) => void) => {
    cb({ uid: 'organizer-1' });
    return () => undefined;
  },
  signInWithPopup: vi.fn(),
  signOut: vi.fn(),
}));

vi.mock('../firebase/client', () => ({
  getFirebaseProblem: () => null,
  initFirebase: () => ({ app: {}, auth: {}, db: {} }),
}));

vi.mock('../ai/device', () => ({
  probeDeviceModel: vi.fn(async () => 'unavailable'),
}));

vi.mock('../firebase/logs', () => ({
  fetchRecentLogs,
  fetchAllLogs,
}));

vi.mock('../features/song/save', () => ({
  fetchSongs,
}));

afterEach(() => {
  cleanup();
  fetchSongs.mockReset();
  fetchRecentLogs.mockClear();
  vi.restoreAllMocks();
});

describe('AdminPage DJ playlist', () => {
  it('displays deduplicated slow-to-dance playlist, flags ambiguous songs, and exports CSV/print', async () => {
    const user = userEvent.setup();
    fetchSongs.mockResolvedValue([
      {
        household_id: 'FAM1',
        slot: 1,
        title: 'Vivir Mi Vida',
        artist: 'Marc Anthony',
        energy: 'dance',
        ambiguous: false,
        raw_text: 'Vivir mi vida',
        ts: '2026-11-25T10:00:00.000Z',
      },
      {
        household_id: 'FAM2',
        slot: 1,
        title: 'vivir mi vida',
        artist: 'Marc Anthony',
        energy: 'dance',
        ambiguous: false,
        raw_text: 'Vivir Mi Vida de Marc Anthony',
        ts: '2026-11-25T10:01:00.000Z',
      },
      {
        household_id: 'FAM3',
        slot: 1,
        title: 'Bésame mucho',
        artist: 'Luis Miguel',
        energy: 'slow',
        ambiguous: false,
        raw_text: 'Besame mucho',
        ts: '2026-11-25T10:02:00.000Z',
      },
      {
        household_id: 'FAM4',
        slot: 2,
        title: null,
        artist: 'Shakira',
        energy: 'dance',
        ambiguous: true,
        raw_text: 'la nueva de Shakira',
        ts: '2026-11-25T10:03:00.000Z',
      },
    ]);

    const printSpy = vi.spyOn(window, 'print').mockImplementation(() => undefined);
    const createUrlSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-csv');
    const revokeUrlSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);

    render(
      <ToastProvider>
        <AdminPage />
      </ToastProvider>,
    );

    expect(await screen.findByRole('heading', { name: 'Lista para el DJ' })).toBeTruthy();
    expect(await screen.findByText('2 canciones únicas de 4 pedidos · 1 por revisar')).toBeTruthy();

    const orderedHeadings = screen
      .getAllByRole('heading', { level: 3 })
      .map((heading) => heading.textContent);
    expect(orderedHeadings).toEqual(['Lentas · para la cena', 'Para bailar', 'Por revisar']);

    expect(screen.getByText('Bésame mucho')).toBeTruthy();
    expect(screen.getByText('Vivir Mi Vida')).toBeTruthy();
    expect(screen.getByText('×2')).toBeTruthy();
    expect(screen.getByText('“la nueva de Shakira”')).toBeTruthy();
    expect(screen.getByText('Revisar')).toBeTruthy();

    await user.click(screen.getByRole('button', { name: 'Descargar CSV' }));
    expect(createUrlSpy).toHaveBeenCalledOnce();
    expect(clickSpy).toHaveBeenCalledOnce();
    expect(revokeUrlSpy).toHaveBeenCalledOnce();

    await user.click(screen.getByRole('button', { name: 'Imprimir' }));
    expect(printSpy).toHaveBeenCalledOnce();
  });
});
