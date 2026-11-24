const MEAL_TAG = /^(vegetarian|vegan|gluten_free|kids_menu|allergy:[a-z][a-z0-9_]{0,31})$/;

export interface RsvpExtraction {
  attending: 'yes' | 'no' | 'maybe';
  party_size: number | null;
  meal_restrictions: string[];
  kids_count: number | null;
  needs_ride: boolean | null;
  ambiguous: boolean;
  confidence: number;
}

function isInteger(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value);
}

export function parseRsvpOutput(raw: string): RsvpExtraction | null {
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
  if (!data || typeof data !== 'object') return null;
  const row = data as Record<string, unknown>;
  if (row.attending !== 'yes' && row.attending !== 'no' && row.attending !== 'maybe') return null;
  if (!(row.party_size === null || (isInteger(row.party_size) && row.party_size >= 1))) return null;
  if (
    !Array.isArray(row.meal_restrictions) ||
    row.meal_restrictions.some((tag) => typeof tag !== 'string' || !MEAL_TAG.test(tag))
  ) {
    return null;
  }
  if (!(row.kids_count === null || (isInteger(row.kids_count) && row.kids_count >= 0))) return null;
  if (!(row.needs_ride === null || typeof row.needs_ride === 'boolean')) return null;
  if (typeof row.ambiguous !== 'boolean') return null;
  if (typeof row.confidence !== 'number' || !Number.isFinite(row.confidence)) return null;
  if (row.confidence < 0 || row.confidence > 1) return null;
  return {
    attending: row.attending,
    party_size: row.party_size,
    meal_restrictions: [...row.meal_restrictions],
    kids_count: row.kids_count,
    needs_ride: row.needs_ride,
    ambiguous: row.ambiguous,
    confidence: row.confidence,
  };
}

export function sameExtraction(a: RsvpExtraction, b: RsvpExtraction): boolean {
  return (
    a.attending === b.attending &&
    a.party_size === b.party_size &&
    a.kids_count === b.kids_count &&
    a.needs_ride === b.needs_ride &&
    a.ambiguous === b.ambiguous &&
    a.meal_restrictions.join('|') === b.meal_restrictions.join('|')
  );
}
