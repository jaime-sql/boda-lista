import { missingEnv, type FirebaseEnv } from '../firebase/config';

export const GUEST_FAILURE = {
  es: {
    title: 'No pudimos responder ahora',
    body: 'Intenta de nuevo en un momento.',
  },
  en: {
    title: "We couldn't answer right now",
    body: 'Please try again in a moment.',
  },
} as const;

function technicalReason(caught: unknown): string {
  if (caught instanceof Error && caught.message.trim()) return caught.message.trim();
  return 'unknown error';
}

/** Logs missing REQUIRED_ENV names, or the App Check / AI error when config is present. */
export function logGuestFailure(caught: unknown, env?: FirebaseEnv): void {
  const names = missingEnv(env);
  if (names.length > 0) {
    console.error(`Firebase disabled: missing ${names.join(', ')}`);
    return;
  }
  console.error(technicalReason(caught));
}
