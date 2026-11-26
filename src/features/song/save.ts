import { addDoc, collection, getDocs, orderBy, query, where } from 'firebase/firestore';
import { getFirestoreDb } from '../../firebase/client';
import type { SongEnergy, SongExtraction } from './parse';

export interface SavedSong {
  household_id: string;
  slot: number; // 1, 2, or 3 — position on the RSVP form
  title: string | null;
  artist: string | null;
  energy: SongEnergy | null;
  ambiguous: boolean;
  raw_text: string;
  ts: string;
}

function clampField(value: string | null, maxLength: number): string | null {
  if (value === null) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  return trimmed.slice(0, maxLength);
}

/** Converts an extracted song request into a Firestore-valid SavedSong document. */
export function toSavedSong(
  householdId: string,
  slot: number,
  extraction: SongExtraction,
  rawText: string,
): SavedSong {
  const safeSlot = Math.min(3, Math.max(1, Math.trunc(slot)));
  return {
    household_id: householdId.trim(),
    slot: safeSlot,
    title: extraction.ambiguous ? null : clampField(extraction.title, 200),
    artist: clampField(extraction.artist, 200),
    energy: extraction.energy,
    ambiguous: extraction.ambiguous,
    raw_text: rawText.trim().slice(0, 500),
    ts: new Date().toISOString(),
  };
}

export async function saveSong(record: SavedSong): Promise<void> {
  if (import.meta.env.VITE_E2E === 'true') return;
  const db = getFirestoreDb();
  await addDoc(collection(db, 'songs'), { ...record });
}

export async function fetchSongs(): Promise<SavedSong[]> {
  const db = getFirestoreDb();
  const snap = await getDocs(query(collection(db, 'songs'), orderBy('ts', 'asc')));
  return snap.docs.map((doc) => doc.data() as SavedSong);
}

export async function fetchSongsByHousehold(householdId: string): Promise<SavedSong[]> {
  const db = getFirestoreDb();
  const snap = await getDocs(
    query(collection(db, 'songs'), where('household_id', '==', householdId)),
  );
  return snap.docs
    .map((doc) => doc.data() as SavedSong)
    .sort((a, b) => a.slot - b.slot);
}
