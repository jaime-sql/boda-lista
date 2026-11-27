import { afterEach, describe, expect, it, vi } from 'vitest';
import type { FirebaseEnv } from '../firebase/config';
import { logGuestFailure } from './guestFailure';

const complete: FirebaseEnv = {
  VITE_FIREBASE_API_KEY: 'api',
  VITE_FIREBASE_AUTH_DOMAIN: 'demo.firebaseapp.com',
  VITE_FIREBASE_PROJECT_ID: 'demo-boda-lista',
  VITE_FIREBASE_STORAGE_BUCKET: 'demo.appspot.com',
  VITE_FIREBASE_MESSAGING_SENDER_ID: '123',
  VITE_FIREBASE_APP_ID: '1:123:web:abc',
  VITE_APPCHECK_SITE_KEY: 'site-key',
};

describe('logGuestFailure', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('names the missing REQUIRED_ENV variable', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    logGuestFailure(new Error('firebase-config-missing'), { ...complete, VITE_APPCHECK_SITE_KEY: ' ' });
    expect(spy).toHaveBeenCalledWith('Firebase disabled: missing VITE_APPCHECK_SITE_KEY');
  });

  it('lists every missing REQUIRED_ENV name', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    logGuestFailure(new Error('firebase-config-missing'), {
      ...complete,
      VITE_FIREBASE_API_KEY: '',
      VITE_APPCHECK_SITE_KEY: '',
    });
    expect(spy).toHaveBeenCalledWith(
      'Firebase disabled: missing VITE_FIREBASE_API_KEY, VITE_APPCHECK_SITE_KEY',
    );
  });

  it('logs an App Check or AI error when every required variable is set', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    logGuestFailure(new Error('app-check/fetch-status-error'), complete);
    expect(spy).toHaveBeenCalledWith('app-check/fetch-status-error');
    expect(spy.mock.calls.flat().join(' ')).not.toContain('Firebase config');
  });
});
