export type SongEnergy = 'slow' | 'medium' | 'dance';

export interface SongExtraction {
  title: string | null;
  artist: string | null;
  energy: SongEnergy | null;
  ambiguous: boolean;
  confidence: number;
}

function normalizeOptionalString(value: unknown): string | null | undefined {
  if (value === null) return null;
  if (typeof value !== 'string') return undefined;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function isSongEnergy(value: unknown): value is SongEnergy | null {
  return value === null || value === 'slow' || value === 'medium' || value === 'dance';
}

/** Parses and validates a single-song JSON response from hybrid inference. */
export function parseSongOutput(raw: string): SongExtraction | null {
  const trimmed = raw
    .trim()
    .replace(/^```(?:json)?/i, '')
    .replace(/```$/i, '')
    .trim();
  let data: unknown;
  try {
    data = JSON.parse(trimmed);
  } catch {
    return null;
  }
  if (!data || typeof data !== 'object' || Array.isArray(data)) return null;
  const row = data as Record<string, unknown>;
  const title = normalizeOptionalString(row.title);
  const artist = normalizeOptionalString(row.artist);
  if (title === undefined || artist === undefined) return null;
  if (!isSongEnergy(row.energy)) return null;
  if (typeof row.ambiguous !== 'boolean') return null;
  if (typeof row.confidence !== 'number' || !Number.isFinite(row.confidence)) return null;
  if (row.confidence < 0 || row.confidence > 1) return null;
  if (row.ambiguous && title !== null) return null;
  if (!row.ambiguous && title === null) return null;
  return {
    title,
    artist,
    energy: row.energy,
    ambiguous: row.ambiguous,
    confidence: row.confidence,
  };
}
