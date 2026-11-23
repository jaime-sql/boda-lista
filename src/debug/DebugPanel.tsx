import { useEffect, useState, useSyncExternalStore } from 'react';
import { probeDeviceModel, type DeviceAvailability } from '../ai/device';
import { appCheckTokenPresence } from '../firebase/client';
import { useOnline } from '../lib/useOnline';
import { RouteBadge } from '../components/RouteBadge';
import { EmptyState, ErrorState, LoadingSkeleton, OfflineState } from '../components/ScreenState';
import { getLastPromptLog, reloadLastPromptLog, subscribeLastPromptLog, type LocalPromptLog } from './sessionLog';

const DEVICE_LABEL: Record<DeviceAvailability, string> = {
  available: 'Disponible',
  downloadable: 'Se puede descargar',
  downloading: 'Descargando',
  unavailable: 'No disponible',
  unsupported: 'Este navegador no incluye el modelo',
};

function useLastLog(): LocalPromptLog | null {
  return useSyncExternalStore(subscribeLastPromptLog, getLastPromptLog, () => null);
}

export function DebugPanel() {
  const online = useOnline();
  const lastLog = useLastLog();
  const [device, setDevice] = useState<DeviceAvailability | null>(null);
  const [tokenPresence, setTokenPresence] = useState<'yes' | 'no' | null>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    reloadLastPromptLog();
  }, []);

  useEffect(() => {
    let alive = true;
    setStatus('loading');
    Promise.all([probeDeviceModel(), appCheckTokenPresence()])
      .then(([nextDevice, presence]) => {
        if (!alive) return;
        setDevice(nextDevice);
        setTokenPresence(presence);
        setStatus('ready');
      })
      .catch(() => {
        if (!alive) return;
        setStatus('error');
      });
    return () => {
      alive = false;
    };
  }, [attempt, online]);

  return (
    <section className="stack gap-3" aria-labelledby="debug-title">
      <h2 id="debug-title" className="section-title">
        Depuración
      </h2>
      <p className="muted">Solo en vistas previas y en desarrollo. No muestra la pregunta ni la respuesta.</p>
      {!online ? (
        <OfflineState detail="Sin red, el token de App Check puede aparecer como no. La ruta guardada en esta sesión sigue visible." />
      ) : null}
      {status === 'loading' ? <LoadingSkeleton label="Revisando el modelo y App Check…" /> : null}
      {status === 'error' ? (
        <ErrorState
          title="No se pudo leer el diagnóstico"
          detail="El modelo del teléfono o App Check no respondieron."
          onRetry={() => setAttempt((value) => value + 1)}
        />
      ) : null}
      {status === 'ready' && device && tokenPresence ? (
        <dl className="kv">
          <dt>Disponibilidad del modelo</dt>
          <dd>
            {DEVICE_LABEL[device]} ({device})
          </dd>
          <dt>Ruta tomada</dt>
          <dd>
            {lastLog ? <RouteBadge route={lastLog.route} /> : 'Sin ruta todavía'}
          </dd>
          <dt>Token de App Check</dt>
          <dd>{tokenPresence}</dd>
        </dl>
      ) : null}
      {status === 'ready' && !lastLog ? (
        <EmptyState
          title="Todavía no hay un registro en esta sesión"
          detail="Cuando alguien pregunte, aquí verás el id del documento y los campos de analytics."
        />
      ) : null}
      {lastLog ? (
        <div className="card pad stack gap-2">
          <h3 className="section-title">Último prompt_log</h3>
          <dl className="kv">
            <dt>id</dt>
            <dd>{lastLog.id}</dd>
            <dt>ts</dt>
            <dd>{lastLog.ts}</dd>
            <dt>feature</dt>
            <dd>{lastLog.feature}</dd>
            <dt>route</dt>
            <dd>{lastLog.route}</dd>
            <dt>fallback_reason</dt>
            <dd>{lastLog.fallback_reason === null ? 'null' : lastLog.fallback_reason}</dd>
            {typeof lastLog.edited_by_guest === 'boolean' ? (
              <>
                <dt>edited_by_guest</dt>
                <dd>{lastLog.edited_by_guest ? 'true' : 'false'}</dd>
              </>
            ) : null}
            <dt>latency_ms</dt>
            <dd>{lastLog.latency_ms}</dd>
            <dt>input_chars</dt>
            <dd>{lastLog.input_chars}</dd>
            <dt>output_chars</dt>
            <dd>{lastLog.output_chars}</dd>
            <dt>model</dt>
            <dd>{lastLog.model}</dd>
            <dt>confidence</dt>
            <dd>{lastLog.confidence === null ? 'null' : lastLog.confidence}</dd>
            <dt>session_id</dt>
            <dd>{lastLog.session_id}</dd>
          </dl>
        </div>
      ) : null}
    </section>
  );
}
