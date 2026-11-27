import { initializeApp, type FirebaseApp } from 'firebase/app';
import {
  getToken,
  initializeAppCheck,
  ReCaptchaEnterpriseProvider,
  type AppCheck,
} from 'firebase/app-check';
import { connectAuthEmulator, getAuth, type Auth } from 'firebase/auth';
import { connectFirestoreEmulator, getFirestore, type Firestore } from 'firebase/firestore';
import { logGuestFailure } from '../lib/guestFailure';
import { applyDebugToken, readFirebaseConfig } from './config';

export interface FirebaseServices {
  app: FirebaseApp;
  auth: Auth;
  db: Firestore;
}

let services: FirebaseServices | null = null;
let appCheck: AppCheck | null = null;
let problem: 'missing' | 'failed' | null = null;
let emulatorsConnected = false;

export function getFirebaseProblem(): 'missing' | 'failed' | null {
  if (services) return null;
  return problem;
}

export function initFirebase(): FirebaseServices | null {
  if (services) return services;
  const config = readFirebaseConfig();
  if (!config) {
    const alreadyMissing = problem === 'missing';
    problem = 'missing';
    if (!alreadyMissing) logGuestFailure(new Error('firebase-config-missing'));
    return null;
  }
  try {
    const app = initializeApp(config.firebase);
    applyDebugToken();
    appCheck = initializeAppCheck(app, {
      provider: new ReCaptchaEnterpriseProvider(config.appCheckSiteKey),
      isTokenAutoRefreshEnabled: true,
    });
    const auth = getAuth(app);
    const db = getFirestore(app);
    if (config.useEmulators && !emulatorsConnected) {
      connectAuthEmulator(auth, 'http://127.0.0.1:9099', { disableWarnings: true });
      connectFirestoreEmulator(db, '127.0.0.1', 8080);
      emulatorsConnected = true;
    }
    services = { app, auth, db };
    problem = null;
    return services;
  } catch (error) {
    problem = 'failed';
    logGuestFailure(error);
    return null;
  }
}

export function getFirebaseApp(): FirebaseApp {
  const ready = initFirebase();
  if (!ready) throw new Error('firebase-config-missing');
  return ready.app;
}

export function getFirestoreDb(): Firestore {
  const ready = initFirebase();
  if (!ready) throw new Error('firebase-config-missing');
  return ready.db;
}

export function getFirebaseAuth(): Auth {
  const ready = initFirebase();
  if (!ready) throw new Error('firebase-config-missing');
  return ready.auth;
}

/** Yes when App Check has issued a token. The token string never leaves this function. */
export async function appCheckTokenPresence(): Promise<'yes' | 'no'> {
  if (!appCheck) return 'no';
  try {
    const result = await getToken(appCheck, false);
    return result.token ? 'yes' : 'no';
  } catch {
    return 'no';
  }
}
