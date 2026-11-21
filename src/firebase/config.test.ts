import { afterEach, describe, expect, it } from 'vitest';
import { applyDebugToken, missingEnv, readFirebaseConfig } from './config';

const complete = {
  VITE_FIREBASE_API_KEY: 'api',
  VITE_FIREBASE_AUTH_DOMAIN: 'demo.firebaseapp.com',
  VITE_FIREBASE_PROJECT_ID: 'demo-boda-lista',
  VITE_FIREBASE_STORAGE_BUCKET: 'demo.appspot.com',
  VITE_FIREBASE_MESSAGING_SENDER_ID: '123',
  VITE_FIREBASE_APP_ID: '1:123:web:abc',
  VITE_APPCHECK_SITE_KEY: 'site-key',
  VITE_FIREBASE_MEASUREMENT_ID: '',
  VITE_USE_EMULATORS: 'true',
};

describe('firebase config', () => {
  afterEach(() => {
    delete (globalThis as { FIREBASE_APPCHECK_DEBUG_TOKEN?: boolean | string }).FIREBASE_APPCHECK_DEBUG_TOKEN;
  });

  it('requires the public web config and the App Check site key', () => {
    expect(missingEnv({ ...complete, VITE_APPCHECK_SITE_KEY: ' ' })).toEqual(['VITE_APPCHECK_SITE_KEY']);
    expect(readFirebaseConfig(complete)?.firebase.projectId).toBe('demo-boda-lista');
    expect(readFirebaseConfig(complete)?.useEmulators).toBe(true);
    expect(readFirebaseConfig(complete)?.firebase.measurementId).toBeUndefined();
  });

  it('accepts a debug token or the true flag and never invents one', () => {
    applyDebugToken({ ...complete, VITE_APPCHECK_DEBUG_TOKEN: 'debug-token' });
    expect(
      (globalThis as { FIREBASE_APPCHECK_DEBUG_TOKEN?: boolean | string }).FIREBASE_APPCHECK_DEBUG_TOKEN,
    ).toBe('debug-token');
    applyDebugToken({ ...complete, VITE_APPCHECK_DEBUG_TOKEN: 'true' });
    expect(
      (globalThis as { FIREBASE_APPCHECK_DEBUG_TOKEN?: boolean | string }).FIREBASE_APPCHECK_DEBUG_TOKEN,
    ).toBe(true);
    delete (globalThis as { FIREBASE_APPCHECK_DEBUG_TOKEN?: boolean | string }).FIREBASE_APPCHECK_DEBUG_TOKEN;
    applyDebugToken({ ...complete, VITE_APPCHECK_DEBUG_TOKEN: ' ' });
    expect(
      (globalThis as { FIREBASE_APPCHECK_DEBUG_TOKEN?: boolean | string }).FIREBASE_APPCHECK_DEBUG_TOKEN,
    ).toBeUndefined();
  });
});
