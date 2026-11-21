import { addDoc, collection, getDocs, limit, orderBy, query } from 'firebase/firestore';
import type { PromptLog } from '../ai/types';
import { getFirestoreDb } from './client';

const COLLECTION = 'prompt_logs';

export async function writePromptLog(entry: PromptLog): Promise<string> {
  const db = getFirestoreDb();
  const ref = await addDoc(collection(db, COLLECTION), { ...entry });
  return ref.id;
}

export async function fetchRecentLogs(): Promise<PromptLog[]> {
  const db = getFirestoreDb();
  const recent = query(collection(db, COLLECTION), orderBy('ts', 'desc'), limit(20));
  const snap = await getDocs(recent);
  return snap.docs.map((doc) => doc.data() as PromptLog);
}
