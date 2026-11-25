import type { SongEnergy } from './parse';
import type { SavedSong } from './save';

export type EnergyBucket = SongEnergy | 'none';

export interface PlaylistTrack {
  key: string;
  title: string;
  artist: string | null;
  energy: SongEnergy | null;
  requests: number;
  households: string[];
  rawTexts: string[];
}

export interface PlaylistGroup {
  energy: SongEnergy | null;
  bucket: EnergyBucket;
  label: string;
  tracks: PlaylistTrack[];
}

export interface DjPlaylist {
  tracks: PlaylistTrack[];
  groups: PlaylistGroup[];
  ambiguous: SavedSong[];
  totalRequests: number;
  clearRequests: number;
  uniqueCount: number;
}

export const ENERGY_ORDER: ReadonlyArray<SongEnergy | null> = ['slow', 'medium', 'dance', null];

export const ENERGY_GROUP_LABEL: Record<EnergyBucket, string> = {
  slow: 'Lentas · para la cena',
  medium: 'Para calentar',
  dance: 'Para bailar',
  none: 'Sin ritmo definido',
};

export const ENERGY_LEVEL: Record<EnergyBucket, number> = {
  slow: 1,
  medium: 3,
  dance: 5,
  none: 0,
};

const ENERGY_CSV_VALUE: Record<EnergyBucket, string> = {
  slow: 'slow',
  medium: 'medium',
  dance: 'dance',
  none: 'sin_definir',
};

export function energyBucket(energy: SongEnergy | null): EnergyBucket {
  return energy ?? 'none';
}

function normalizeKeyPart(value: string): string {
  const cleaned = value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return cleaned || value.trim().toLowerCase();
}

function pickDisplayText(candidates: string[]): string {
  const counts = new Map<string, number>();
  for (const item of candidates) {
    const trimmed = item.trim();
    if (!trimmed) continue;
    counts.set(trimmed, (counts.get(trimmed) ?? 0) + 1);
  }
  const scored = [...counts.entries()].map(([value, count]) => {
    const hasAccent = /[^\x00-\x7F]/.test(value) ? 1 : 0;
    const hasUpper = /\p{Lu}/u.test(value) ? 1 : 0;
    return { value, count, hasAccent, hasUpper };
  });
  scored.sort(
    (a, b) =>
      b.count - a.count ||
      b.hasAccent - a.hasAccent ||
      b.hasUpper - a.hasUpper ||
      a.value.localeCompare(b.value, 'es'),
  );
  return scored[0]?.value ?? '';
}

function resolveEnergy(energies: Array<SongEnergy | null>): SongEnergy | null {
  const counts = new Map<SongEnergy, number>();
  for (const energy of energies) {
    if (!energy) continue;
    counts.set(energy, (counts.get(energy) ?? 0) + 1);
  }
  if (counts.size === 0) return null;
  let best: SongEnergy | null = null;
  let bestCount = -1;
  for (const tier of ['slow', 'medium', 'dance'] as const) {
    const count = counts.get(tier) ?? 0;
    if (count > bestCount) {
      best = tier;
      bestCount = count;
    }
  }
  return best;
}

type Accumulator = {
  key: string;
  titles: string[];
  artists: string[];
  energies: Array<SongEnergy | null>;
  requests: number;
  households: string[];
  rawTexts: string[];
};

/** Deduplicates clear song requests and orders the playlist from slow to dance. */
export function buildDjPlaylist(songs: readonly SavedSong[]): DjPlaylist {
  const clear: SavedSong[] = [];
  const ambiguous: SavedSong[] = [];

  for (const song of songs) {
    const title = song.title?.trim() ?? '';
    if (song.ambiguous || title.length === 0) {
      ambiguous.push(song);
    } else {
      clear.push(song);
    }
  }

  // Allow an artist-less request to merge when that normalized title maps uniquely to one artist.
  const artistsByTitle = new Map<string, Set<string>>();
  for (const song of clear) {
    const tKey = normalizeKeyPart(song.title!);
    const aKey = song.artist ? normalizeKeyPart(song.artist) : '';
    if (!aKey) continue;
    if (!artistsByTitle.has(tKey)) artistsByTitle.set(tKey, new Set());
    artistsByTitle.get(tKey)!.add(aKey);
  }

  const buckets = new Map<string, Accumulator>();
  for (const song of clear) {
    const tKey = normalizeKeyPart(song.title!);
    let aKey = song.artist ? normalizeKeyPart(song.artist) : '';
    if (!aKey) {
      const knownArtists = artistsByTitle.get(tKey);
      if (knownArtists && knownArtists.size === 1) {
        aKey = [...knownArtists][0] ?? '';
      }
    }
    const key = `${tKey}::${aKey}`;
    let acc = buckets.get(key);
    if (!acc) {
      acc = {
        key,
        titles: [],
        artists: [],
        energies: [],
        requests: 0,
        households: [],
        rawTexts: [],
      };
      buckets.set(key, acc);
    }
    acc.requests += 1;
    acc.titles.push(song.title!.trim());
    if (song.artist?.trim()) acc.artists.push(song.artist.trim());
    acc.energies.push(song.energy);
    if (song.household_id && !acc.households.includes(song.household_id)) {
      acc.households.push(song.household_id);
    }
    const raw = song.raw_text.trim();
    if (raw && !acc.rawTexts.includes(raw)) {
      acc.rawTexts.push(raw);
    }
  }

  const tracks: PlaylistTrack[] = [...buckets.values()].map((acc) => ({
    key: acc.key,
    title: pickDisplayText(acc.titles),
    artist: acc.artists.length > 0 ? pickDisplayText(acc.artists) : null,
    energy: resolveEnergy(acc.energies),
    requests: acc.requests,
    households: acc.households,
    rawTexts: acc.rawTexts,
  }));

  const groups: PlaylistGroup[] = [];
  for (const energy of ENERGY_ORDER) {
    const groupTracks = tracks
      .filter((track) => track.energy === energy)
      .sort(
        (a, b) =>
          b.requests - a.requests ||
          a.title.localeCompare(b.title, 'es', { sensitivity: 'base' }) ||
          (a.artist ?? '').localeCompare(b.artist ?? '', 'es', { sensitivity: 'base' }),
      );
    if (groupTracks.length === 0) continue;
    const bucket = energyBucket(energy);
    groups.push({
      energy,
      bucket,
      label: ENERGY_GROUP_LABEL[bucket],
      tracks: groupTracks,
    });
  }

  const orderedTracks = groups.flatMap((group) => group.tracks);
  const orderedAmbiguous = [...ambiguous].sort((a, b) => a.ts.localeCompare(b.ts));

  return {
    tracks: orderedTracks,
    groups,
    ambiguous: orderedAmbiguous,
    totalRequests: songs.length,
    clearRequests: clear.length,
    uniqueCount: orderedTracks.length,
  };
}

function escapeCsvCell(value: string | number): string {
  let text = String(value);
  if (/^[=+\-@\t\r]/.test(text)) {
    text = `'${text}`;
  }
  if (/[",\n\r]/.test(text) || text.startsWith("'")) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

/** Formats the ordered DJ playlist and ambiguous items as RFC-4180 CSV. */
export function playlistToCsv(playlist: DjPlaylist): string {
  const header = ['orden', 'energia', 'titulo', 'artista', 'pedidos', 'hogares', 'estado', 'texto_original'];
  const rows: string[] = [header.join(',')];

  playlist.tracks.forEach((track, index) => {
    const bucket = energyBucket(track.energy);
    rows.push(
      [
        index + 1,
        ENERGY_CSV_VALUE[bucket],
        track.title,
        track.artist ?? '',
        track.requests,
        track.households.join(';'),
        'lista',
        track.rawTexts.join(' | '),
      ]
        .map(escapeCsvCell)
        .join(','),
    );
  });

  for (const item of playlist.ambiguous) {
    const bucket = energyBucket(item.energy);
    rows.push(
      [
        '',
        ENERGY_CSV_VALUE[bucket],
        '',
        item.artist ?? '',
        1,
        item.household_id,
        'revisar',
        item.raw_text,
      ]
        .map(escapeCsvCell)
        .join(','),
    );
  }

  return rows.join('\r\n');
}

/** Triggers a browser CSV download for the compiled DJ playlist. */
export function downloadPlaylistCsv(
  playlist: DjPlaylist,
  filename = 'boda-lista-canciones-dj.csv',
): void {
  const csv = playlistToCsv(playlist);
  const blob = new Blob(['\uFEFF', csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
