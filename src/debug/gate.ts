export type DebugEnv = {
  DEV: boolean;
  VITE_ENABLE_DEBUG?: string;
};

export function currentDebugEnv(): DebugEnv {
  return {
    DEV: import.meta.env.DEV,
    VITE_ENABLE_DEBUG: import.meta.env.VITE_ENABLE_DEBUG,
  };
}

export function isDebugBuild(env: DebugEnv): boolean {
  return env.DEV || env.VITE_ENABLE_DEBUG === 'true';
}

export function isDebugRequest(search: string): boolean {
  const query = search.startsWith('?') ? search.slice(1) : search;
  return new URLSearchParams(query).get('debug') === '1';
}

export function isDebugPanelEnabled(env: DebugEnv, search: string): boolean {
  return isDebugBuild(env) && isDebugRequest(search);
}
