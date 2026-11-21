export const REQUIRED_ENV = [
  'VITE_FIREBASE_API_KEY',
  'VITE_FIREBASE_AUTH_DOMAIN',
  'VITE_FIREBASE_PROJECT_ID',
  'VITE_FIREBASE_STORAGE_BUCKET',
  'VITE_FIREBASE_MESSAGING_SENDER_ID',
  'VITE_FIREBASE_APP_ID',
  'VITE_APPCHECK_SITE_KEY',
] as const;

export type RequiredEnvName = (typeof REQUIRED_ENV)[number];

export interface FirebaseEnv {
  VITE_FIREBASE_API_KEY?: string;
  VITE_FIREBASE_AUTH_DOMAIN?: string;
  VITE_FIREBASE_PROJECT_ID?: string;
  VITE_FIREBASE_STORAGE_BUCKET?: string;
  VITE_FIREBASE_MESSAGING_SENDER_ID?: string;
  VITE_FIREBASE_APP_ID?: string;
  VITE_FIREBASE_MEASUREMENT_ID?: string;
  VITE_APPCHECK_SITE_KEY?: string;
  VITE_APPCHECK_DEBUG_TOKEN?: string;
  VITE_USE_EMULATORS?: string;
  VITE_GEMINI_CLOUD_MODEL?: string;
  VITE_ENABLE_DEBUG?: string;
}

export interface FirebasePublicConfig {
  apiKey: string;
  authDomain: string;
  projectId: string;
  storageBucket: string;
  messagingSenderId: string;
  appId: string;
  measurementId?: string;
}

export interface AppConfig {
  firebase: FirebasePublicConfig;
  appCheckSiteKey: string;
  useEmulators: boolean;
}

function value(env: FirebaseEnv, key: keyof FirebaseEnv): string {
  return env[key]?.trim() ?? '';
}

export function missingEnv(env: FirebaseEnv = import.meta.env): RequiredEnvName[] {
  return REQUIRED_ENV.filter((key) => value(env, key).length === 0);
}

export function readFirebaseConfig(env: FirebaseEnv = import.meta.env): AppConfig | null {
  if (missingEnv(env).length > 0) return null;
  const measurementId = value(env, 'VITE_FIREBASE_MEASUREMENT_ID');
  return {
    firebase: {
      apiKey: value(env, 'VITE_FIREBASE_API_KEY'),
      authDomain: value(env, 'VITE_FIREBASE_AUTH_DOMAIN'),
      projectId: value(env, 'VITE_FIREBASE_PROJECT_ID'),
      storageBucket: value(env, 'VITE_FIREBASE_STORAGE_BUCKET'),
      messagingSenderId: value(env, 'VITE_FIREBASE_MESSAGING_SENDER_ID'),
      appId: value(env, 'VITE_FIREBASE_APP_ID'),
      ...(measurementId ? { measurementId } : {}),
    },
    appCheckSiteKey: value(env, 'VITE_APPCHECK_SITE_KEY'),
    useEmulators: value(env, 'VITE_USE_EMULATORS') === 'true',
  };
}

export function applyDebugToken(env: FirebaseEnv = import.meta.env): void {
  const raw = env.VITE_APPCHECK_DEBUG_TOKEN?.trim();
  if (!raw) return;
  const token = raw === 'true' ? true : raw;
  (globalThis as { FIREBASE_APPCHECK_DEBUG_TOKEN?: boolean | string }).FIREBASE_APPCHECK_DEBUG_TOKEN =
    token;
}
