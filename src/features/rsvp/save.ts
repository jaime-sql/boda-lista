import { addDoc, collection } from 'firebase/firestore';
import { getFirestoreDb } from '../../firebase/client';
import type { RsvpExtraction } from './parse';

export interface SavedRsvp {
  household_id: string;
  attending: RsvpExtraction['attending'];
  party_size: number | null;
  meal_restrictions: string[];
  kids_count: number | null;
  needs_ride: boolean | null;
  ambiguous: boolean;
  edited: boolean;
  ts: string;
}

export function toSavedRsvp(householdId: string, fields: RsvpExtraction, edited: boolean): SavedRsvp {
  return {
    household_id: householdId,
    attending: fields.attending,
    party_size: fields.party_size,
    meal_restrictions: fields.meal_restrictions,
    kids_count: fields.kids_count,
    needs_ride: fields.needs_ride,
    ambiguous: fields.ambiguous,
    edited,
    ts: new Date().toISOString(),
  };
}

export async function saveRsvp(record: SavedRsvp): Promise<void> {
  if (import.meta.env.VITE_E2E === 'true') return;
  const db = getFirestoreDb();
  await addDoc(collection(db, 'rsvps'), { ...record });
}
