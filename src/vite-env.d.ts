/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_FIREBASE_API_KEY?: string;
  readonly VITE_FIREBASE_AUTH_DOMAIN?: string;
  readonly VITE_FIREBASE_PROJECT_ID?: string;
  readonly VITE_FIREBASE_STORAGE_BUCKET?: string;
  readonly VITE_FIREBASE_MESSAGING_SENDER_ID?: string;
  readonly VITE_FIREBASE_APP_ID?: string;
  readonly VITE_FIREBASE_MEASUREMENT_ID?: string;
  readonly VITE_APPCHECK_SITE_KEY?: string;
  readonly VITE_APPCHECK_DEBUG_TOKEN?: string;
  readonly VITE_USE_EMULATORS?: string;
  readonly VITE_GEMINI_CLOUD_MODEL?: string;
  readonly VITE_ENABLE_DEBUG?: string;
  readonly VITE_E2E?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

interface LanguageModelGlobal {
  availability: () => Promise<string>;
}

interface Window {
  LanguageModel?: LanguageModelGlobal;
}
