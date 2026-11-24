import { useEffect, useState } from 'react';
import { GoogleAuthProvider, onAuthStateChanged, signInWithPopup, signOut, type User } from 'firebase/auth';
import { probeDeviceModel, type DeviceAvailability } from '../ai/device';
import type { PromptLog } from '../ai/types';
import { InfoDialog } from '../components/InfoDialog';
import { RouteBadge } from '../components/RouteBadge';
import { EmptyState, ErrorState, LoadingSkeleton, OfflineState } from '../components/ScreenState';
import { useToast } from '../components/ToastProvider';
import { getFirebaseProblem, initFirebase } from '../firebase/client';
import { fetchRecentLogs } from '../firebase/logs';
import { useOnline } from '../lib/useOnline';

const DEVICE_LABEL: Record<DeviceAvailability, string> = {
  available: 'Disponible',
  downloadable: 'Se puede descargar',
  downloading: 'Descargando',
  unavailable: 'No disponible',
  unsupported: 'Este navegador no incluye el modelo',
};

export function AdminPage() {
  const online = useOnline();
  const publish = useToast();
  const [device, setDevice] = useState<DeviceAvailability | 'loading' | 'error'>('loading');
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [authError, setAuthError] = useState(false);
  const [logs, setLogs] = useState<PromptLog[]>([]);
  const [logsStatus, setLogsStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [reload, setReload] = useState(0);
  const problem = getFirebaseProblem();

  useEffect(() => {
    let alive = true;
    setDevice('loading');
    probeDeviceModel()
      .then((status) => {
        if (alive) setDevice(status);
      })
      .catch(() => {
        if (alive) setDevice('error');
      });
    return () => {
      alive = false;
    };
  }, [reload]);

  useEffect(() => {
    const services = initFirebase();
    if (!services) {
      setAuthReady(true);
      return;
    }
    return onAuthStateChanged(services.auth, (next) => {
      setUser(next);
      setAuthReady(true);
    });
  }, []);

  useEffect(() => {
    if (!user || !online) return;
    let alive = true;
    setLogsStatus('loading');
    fetchRecentLogs()
      .then((rows) => {
        if (!alive) return;
        setLogs(rows);
        setLogsStatus('ready');
      })
      .catch(() => {
        if (!alive) return;
        setLogsStatus('error');
      });
    return () => {
      alive = false;
    };
  }, [user, online, reload]);

  async function signIn() {
    setAuthError(false);
    try {
      const services = initFirebase();
      if (!services) {
        setAuthError(true);
        return;
      }
      await signInWithPopup(services.auth, new GoogleAuthProvider());
      publish({ title: 'Sesión iniciada', description: 'Ya puedes ver los registros.' });
    } catch {
      setAuthError(true);
      publish({ title: 'No se pudo entrar', description: 'Inténtalo de nuevo.' });
    }
  }

  async function signOutUser() {
    const services = initFirebase();
    if (!services) return;
    await signOut(services.auth);
  }

  return (
    <div className="page-narrow">
      <div className="weave" />
      <h1 className="page-title">Diagnóstico</h1>
      <p className="muted">La página de invitados no pide cuenta. Aquí se revisa el modelo y los registros.</p>
      <InfoDialog trigger="Qué se guarda" title="Qué se guarda">
        <p>
          Hora, función, ruta, motivo, latencia, tamaños, modelo, confianza y un id de sesión. Nunca el texto de
          la pregunta ni de la respuesta, ni nombres de invitados.
        </p>
      </InfoDialog>
      {!online ? (
        <OfflineState detail="Sin red no se pueden leer los registros. El estado del modelo en el teléfono sí se puede ver." />
      ) : null}
      <section className="stack gap-3" aria-labelledby="device-title">
        <h2 id="device-title" className="section-title">
          Modelo en el dispositivo
        </h2>
        {device === 'loading' ? <LoadingSkeleton label="Revisando el modelo en el dispositivo…" /> : null}
        {device === 'error' ? (
          <ErrorState
            title="No se pudo revisar el modelo"
            detail="Este navegador no respondió al consultar Gemini Nano."
            onRetry={() => setReload((value) => value + 1)}
          />
        ) : null}
        {device !== 'loading' && device !== 'error' ? (
          <p>
            {DEVICE_LABEL[device]} ({device})
          </p>
        ) : null}
      </section>
      <section className="stack gap-3" aria-labelledby="logs-title">
        <h2 id="logs-title" className="section-title">
          Últimos registros
        </h2>
        {!authReady ? <LoadingSkeleton label="Revisando la sesión…" /> : null}
        {authReady && problem ? (
          <ErrorState
            title="Falta configuración"
            detail="Revisa las variables de Firebase y App Check antes de entrar."
            onRetry={() => window.location.reload()}
          />
        ) : null}
        {authError ? (
          <ErrorState
            title="No se pudo entrar"
            detail="Google no completó el acceso. La página de invitados sigue disponible sin cuenta."
            onRetry={() => void signIn()}
          />
        ) : null}
        {authReady && !problem && !user ? (
          <EmptyState
            title="Los registros están reservados"
            detail="Entra con Google para ver los últimos 20. Quien invita no necesita cuenta."
          />
        ) : null}
        {authReady && !user ? (
          <button type="button" className="btn btn-primary" onClick={() => void signIn()}>
            Entrar con Google
          </button>
        ) : null}
        {user ? (
          <div className="row gap-2">
            <button type="button" className="btn btn-secondary" onClick={() => void signOutUser()}>
              Salir
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => setReload((value) => value + 1)}>
              Actualizar
            </button>
          </div>
        ) : null}
        {user && online && logsStatus === 'loading' ? <LoadingSkeleton label="Cargando registros…" /> : null}
        {user && online && logsStatus === 'error' ? (
          <ErrorState
            title="No se pudieron leer los registros"
            detail="Entra con la cuenta de la boda e inténtalo de nuevo."
            onRetry={() => setReload((value) => value + 1)}
          />
        ) : null}
        {user && online && logsStatus === 'ready' && logs.length === 0 ? (
          <EmptyState
            title="Todavía no hay registros"
            detail="Aparecen cuando alguien hace una pregunta."
          />
        ) : null}
        {user && online && logsStatus === 'ready' && logs.length > 0 ? (
          <ol className="stack gap-3">
            {logs.map((log, index) => (
              <li key={`${log.ts}-${log.session_id}-${index}`} className="card pad stack gap-2">
                <RouteBadge route={log.route} />
                <dl className="kv">
                  <dt>ts</dt>
                  <dd>{log.ts}</dd>
                  <dt>feature</dt>
                  <dd>{log.feature}</dd>
                  <dt>route</dt>
                  <dd>{log.route}</dd>
                  <dt>fallback_reason</dt>
                  <dd>{log.fallback_reason === null ? 'null' : log.fallback_reason}</dd>
                  <dt>latency_ms</dt>
                  <dd>{log.latency_ms}</dd>
                  <dt>input_chars</dt>
                  <dd>{log.input_chars}</dd>
                  <dt>output_chars</dt>
                  <dd>{log.output_chars}</dd>
                  <dt>model</dt>
                  <dd>{log.model === null ? 'null' : log.model}</dd>
                  {log.lang ? (
                    <>
                      <dt>lang</dt>
                      <dd>{log.lang}</dd>
                    </>
                  ) : null}
                  <dt>confidence</dt>
                  <dd>{log.confidence === null ? 'null' : log.confidence}</dd>
                  <dt>session_id</dt>
                  <dd>{log.session_id}</dd>
                </dl>
              </li>
            ))}
          </ol>
        ) : null}
      </section>
    </div>
  );
}
