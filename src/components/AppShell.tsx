import type { ReactNode } from 'react';
import { NavLink, useSearchParams } from 'react-router-dom';
import { DebugPanel } from '../debug/DebugPanel';
import { currentDebugEnv, isDebugPanelEnabled, type DebugEnv } from '../debug/gate';

type AppShellProps = {
  children: ReactNode;
  debugEnv?: DebugEnv;
};

export function AppShell({ children, debugEnv = currentDebugEnv() }: AppShellProps) {
  const [params] = useSearchParams();
  const debug = isDebugPanelEnabled(debugEnv, `?${params.toString()}`);
  const search = debug ? '?debug=1' : '';

  return (
    <div className="app">
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>
      <header className="header">
        <NavLink className="brand" to={{ pathname: '/', search }} end>
          Boda Lista
        </NavLink>
        <nav className="nav" aria-label="Secciones">
          <NavLink className="nav-link" to={{ pathname: '/', search }} end>
            Invitados
          </NavLink>
          <NavLink className="nav-link" to={{ pathname: '/admin', search }}>
            Diagnóstico
          </NavLink>
        </nav>
      </header>
      <main id="contenido" className="main">
        <div className="stack">
          {children}
          {debug ? <DebugPanel /> : null}
        </div>
      </main>
    </div>
  );
}
