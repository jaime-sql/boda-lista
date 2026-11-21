import type { ReactNode } from 'react';
import { useSearchParams } from 'react-router-dom';
import { DebugPanel } from '../debug/DebugPanel';
import { currentDebugEnv, isDebugPanelEnabled, type DebugEnv } from '../debug/gate';

type AppShellProps = {
  children: ReactNode;
  debugEnv?: DebugEnv;
};

export function AppShell({ children, debugEnv = currentDebugEnv() }: AppShellProps) {
  const [params] = useSearchParams();
  const debug = isDebugPanelEnabled(debugEnv, `?${params.toString()}`);

  return (
    <div className="app">
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>
      {children}
      {debug ? (
        <div className="page-narrow">
          <DebugPanel />
        </div>
      ) : null}
    </div>
  );
}
