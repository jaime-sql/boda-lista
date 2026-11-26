import { describe, expect, it } from 'vitest';
import { buildDjPlaylist, playlistToCsv } from './playlist';
import type { SavedSong } from './save';

function song(overrides: Partial<SavedSong> = {}): SavedSong {
  return {
    household_id: 'FAM-1',
    slot: 1,
    title: 'Vivir Mi Vida',
    artist: 'Marc Anthony',
    energy: 'dance',
    ambiguous: false,
    raw_text: 'Vivir mi vida de Marc Anthony',
    ts: '2026-11-25T10:00:00.000Z',
    ...overrides,
  };
}

describe('buildDjPlaylist', () => {
  it('deduplicates across case, diacritics, and inferred single artist while separating ambiguous items', () => {
    const songs: SavedSong[] = [
      song({ household_id: 'FAM-1', title: 'vivir mi vida', artist: 'marc anthony', energy: 'dance' }),
      song({ household_id: 'FAM-2', title: 'Vivir Mi Vida!', artist: 'Marc Anthony', energy: 'dance' }),
      song({ household_id: 'FAM-3', title: 'Vivir Mi Vida', artist: null, energy: null }),
      song({
        household_id: 'FAM-4',
        title: 'Bésame mucho',
        artist: 'Luis Miguel',
        energy: 'slow',
        raw_text: 'Besame mucho de Luis Miguel',
      }),
      song({
        household_id: 'FAM-5',
        title: 'Besame Mucho',
        artist: 'Luis Miguel',
        energy: 'slow',
        raw_text: 'Bésame mucho - Luis Miguel',
      }),
      song({
        household_id: 'FAM-6',
        title: 'Propuesta Indecente',
        artist: 'Romeo Santos',
        energy: 'medium',
        raw_text: 'Propuesta indecente',
      }),
      song({
        household_id: 'FAM-7',
        title: null,
        artist: 'Marc Anthony',
        energy: 'dance',
        ambiguous: true,
        raw_text: 'la de Marc Anthony que siempre ponen',
        ts: '2026-11-25T09:00:00.000Z',
      }),
    ];

    const playlist = buildDjPlaylist(songs);
    expect(playlist.totalRequests).toBe(7);
    expect(playlist.clearRequests).toBe(6);
    expect(playlist.uniqueCount).toBe(3);
    expect(playlist.ambiguous).toHaveLength(1);
    expect(playlist.ambiguous[0]?.raw_text).toBe('la de Marc Anthony que siempre ponen');

    // Ordered slow -> medium -> dance
    expect(playlist.groups.map((g) => g.energy)).toEqual(['slow', 'medium', 'dance']);
    expect(playlist.tracks.map((t) => t.energy)).toEqual(['slow', 'medium', 'dance']);

    // Check deduplication & preferred accented/capitalized form
    const slowTrack = playlist.tracks[0];
    expect(slowTrack?.title).toBe('Bésame mucho');
    expect(slowTrack?.requests).toBe(2);
    expect(slowTrack?.households).toEqual(['FAM-4', 'FAM-5']);

    const danceTrack = playlist.tracks[2];
    expect(danceTrack?.title).toBe('Vivir Mi Vida');
    expect(danceTrack?.artist).toBe('Marc Anthony');
    expect(danceTrack?.requests).toBe(3);
    expect(danceTrack?.households).toEqual(['FAM-1', 'FAM-2', 'FAM-3']);
  });

  it('keeps distinct artists separate for identically titled songs and sorts within tiers', () => {
    const songs: SavedSong[] = [
      song({ household_id: 'A', title: 'Héroe', artist: 'Enrique Iglesias', energy: 'slow' }),
      song({ household_id: 'B', title: 'Héroe', artist: 'Mariah Carey', energy: 'slow' }),
      song({ household_id: 'C', title: 'Perfect', artist: 'Ed Sheeran', energy: 'slow' }),
      song({ household_id: 'D', title: 'Perfect', artist: 'Ed Sheeran', energy: 'slow' }),
    ];
    const playlist = buildDjPlaylist(songs);
    expect(playlist.uniqueCount).toBe(3);
    expect(playlist.tracks[0]?.title).toBe('Perfect');
    expect(playlist.tracks[0]?.requests).toBe(2);
    expect(playlist.tracks.slice(1).map((t) => t.artist)).toEqual(['Enrique Iglesias', 'Mariah Carey']);
  });

  it('renders RFC-4180 CSV with slow-to-dance order, review rows, and formula-injection escaping', () => {
    const playlist = buildDjPlaylist([
      song({ household_id: 'FAM-1', title: 'Suavemente', artist: 'Elvis Crespo', energy: 'dance' }),
      song({
        household_id: 'FAM-2',
        title: 'A Puro Dolor',
        artist: 'Son by Four',
        energy: 'slow',
        raw_text: 'A puro dolor, lenta',
      }),
      song({
        household_id: 'FAM-3',
        title: null,
        artist: null,
        energy: null,
        ambiguous: true,
        raw_text: '=SUM(1,2) "esa canción"',
      }),
    ]);

    const csv = playlistToCsv(playlist);
    const lines = csv.split('\r\n');
    expect(lines[0]).toBe('orden,energia,titulo,artista,pedidos,hogares,estado,texto_original');
    expect(lines[1]).toBe('1,slow,A Puro Dolor,Son by Four,1,FAM-2,lista,"A puro dolor, lenta"');
    expect(lines[2]).toBe('2,dance,Suavemente,Elvis Crespo,1,FAM-1,lista,Vivir mi vida de Marc Anthony');
    expect(lines[3]).toBe(',sin_definir,,,1,FAM-3,revisar,"\'=SUM(1,2) ""esa canción"""');
  });
});
