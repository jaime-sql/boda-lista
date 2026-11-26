import { useEffect, useMemo, useState } from 'react';
import { GoogleAuthProvider, onAuthStateChanged, signInWithPopup, signOut, type User } from 'firebase/auth';
import { probeDeviceModel, type DeviceAvailability } from '../ai/device';
import type { PromptLog } from '../ai/types';
import { Icon } from '../components/Icon';
import { InfoDialog } from '../components/InfoDialog';
import { RouteBadge } from '../components/RouteBadge';
import { EmptyState, ErrorState, LoadingSkeleton, OfflineState } from '../components/ScreenState';
import { useToast } from '../components/ToastProvider';
import { getFirebaseProblem, initFirebase } from '../firebase/client';
import { fetchRecentLogs } from '../firebase/logs';
import {
  buildDjPlaylist,
  downloadPlaylistCsv,
  ENERGY_LEVEL,
  energyBucket,
} from '../features/song/playlist';
import { fetchSongs, type SavedSong } from '../features/song/save';
import { useOnline } from '../lib/useOnline';
import '../styles/admin.css';

const DEVICE_LABEL: Record<DeviceAvailability, string> = {
  available: 'Disponible',
  downloadable: 'Se puede descargar',
  downloading: 'Descargando',
  unavailable: 'No disponible',
  unsupported: 'Este navegador no incluye el modelo',
};

const EQ_HEIGHTS = ['dj-eq-1', 'dj-eq-2', 'dj-eq-3', 'dj-eq-4', 'dj-eq-5'] as const;

function plural(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`;
}

export function AdminPage() {
  const online = useOnline();
  const publish = useToast();
  const [device, setDevice] = useState<DeviceAvailability | 'loading' | 'error'>('loading');
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [authError, setAuthError] = useState(false);
  const [logs, setLogs] = useState<PromptLog[]>([]);
  const [logsStatus, setLogsStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [songs, setSongs] = useState<SavedSong[]>([]);
  const [songsStatus, setSongsStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
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

  useEffect(() => {
    if (!user || !online) return;
    let alive = true;
    setSongsStatus('loading');
    fetchSongs()
      .then((rows) => {
        if (!alive) return;
        setSongs(rows);
        setSongsStatus('ready');
      })
      .catch(() => {
        if (!alive) return;
        setSongsStatus('error');
      });
    return () => {
      alive = false;
    };
  }, [user, online, reload]);

  const playlist = useMemo(() => buildDjPlaylist(songs), [songs]);

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

  function handleDownloadCsv() {
    downloadPlaylistCsv(playlist);
    publish({ title: 'Lista descargada', description: 'Archivo CSV listo para el DJ.' });
  }

  let trackCounter = 0;

  return (
    <div className="page-narrow">
      <div className="weave no-print" />
      <h1 className="page-title no-print">Diagnóstico</h1>
      <p className="muted no-print">La página de invitados no pide cuenta. Aquí se revisa el modelo y los registros.</p>
      <div className="no-print">
        <InfoDialog trigger="Qué se guarda" title="Qué se guarda">
          <p>
            Hora, función, ruta, motivo, latencia, tamaños, modelo, confianza y un id de sesión. Nunca el texto de
            la pregunta ni de la respuesta, ni nombres de invitados.
          </p>
        </InfoDialog>
      </div>
      {!online ? (
        <div className="no-print">
          <OfflineState detail="Sin red no se pueden leer los registros. El estado del modelo en el teléfono sí se puede ver." />
        </div>
      ) : null}
      <section className="stack gap-3 no-print" aria-labelledby="device-title">
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
      <section className="stack gap-3 no-print" aria-labelledby="auth-title">
        <h2 id="auth-title" className="section-title">
          Cuenta de organización
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
      </section>

      {user ? (
        <section className="stack gap-3 dj-section" aria-labelledby="songs-title">
          <div className="dj-title-row">
            <Icon name="music" size={22} />
            <h2 id="songs-title" className="section-title">
              Lista para el DJ
            </h2>
          </div>
          {online && songsStatus === 'loading' ? <LoadingSkeleton label="Cargando canciones…" /> : null}
          {online && songsStatus === 'error' ? (
            <ErrorState
              title="No se pudieron leer las canciones"
              detail="Entra con la cuenta de la boda e inténtalo de nuevo."
              onRetry={() => setReload((value) => value + 1)}
            />
          ) : null}
          {songsStatus === 'ready' && songs.length === 0 ? (
            <EmptyState
              title="Todavía no hay canciones"
              detail="Aparecen cuando alguien pide canciones en su confirmación."
            />
          ) : null}
          {songsStatus === 'ready' && songs.length > 0 ? (
            <div className="card">
              <div className="dj-head">
                <p className="muted sm">
                  {plural(playlist.uniqueCount, 'canción única', 'canciones únicas')} de{' '}
                  {plural(playlist.totalRequests, 'pedido', 'pedidos')}
                  {playlist.ambiguous.length > 0 ? ` · ${playlist.ambiguous.length} por revisar` : ''}
                </p>
              </div>
              {playlist.tracks.length > 0 ? (
                <div className="dj-arrow">
                  <span>Lentas</span>
                  <span aria-hidden="true">→</span>
                  <span>Para bailar</span>
                </div>
              ) : null}
              {playlist.groups.map((group) => {
                const level = ENERGY_LEVEL[group.bucket];
                return (
                  <div key={group.bucket}>
                    <h3 className="dj-group-title">{group.label}</h3>
                    <ol className="dj-playlist">
                      {group.tracks.map((track) => {
                        trackCounter += 1;
                        const num = String(trackCounter).padStart(2, '0');
                        const trackLevel = ENERGY_LEVEL[energyBucket(track.energy)];
                        return (
                          <li key={track.key} className="dj-trk">
                            <span className="dj-tn">{num}</span>
                            <span className="dj-tt">
                              <b>{track.title}</b>
                              <span className="muted sm">{track.artist ?? 'Artista sin confirmar'}</span>
                            </span>
                            <span className="dj-eq" role="img" aria-label={`Energía ${level} de 5`}>
                              {EQ_HEIGHTS.map((heightClass, index) => (
                                <b
                                  key={heightClass}
                                  className={`${heightClass}${index + 1 <= trackLevel ? ' on' : ''}`}
                                />
                              ))}
                            </span>
                            <span className="dj-req">×{track.requests}</span>
                          </li>
                        );
                      })}
                    </ol>
                  </div>
                );
              })}
              {playlist.ambiguous.length > 0 ? (
                <div>
                  <h3 className="dj-group-title amb">Por revisar</h3>
                  <ul className="dj-playlist">
                    {playlist.ambiguous.map((song, index) => (
                      <li key={`${song.household_id}-${song.slot}-${song.ts}-${index}`} className="dj-trk amb">
                        <Icon name="flag" size={18} />
                        <span className="dj-tt">
                          <b>“{song.raw_text}”</b>
                          <span className="sm">
                            {song.artist ? `${song.artist} · ` : ''}
                            Sin título claro · {song.household_id}
                          </span>
                        </span>
                        <span className="badge badge-review">Revisar</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              <div className="dj-actions no-print">
                <button type="button" className="btn btn-primary" onClick={handleDownloadCsv}>
                  <Icon name="download" size={20} />
                  Descargar CSV
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => window.print()}>
                  <Icon name="printer" size={20} />
                  Imprimir
                </button>
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {user ? (
        <section className="stack gap-3 no-print" aria-labelledby="logs-title">
          <h2 id="logs-title" className="section-title">
            Últimos registros
          </h2>
          {online && logsStatus === 'loading' ? <LoadingSkeleton label="Cargando registros…" /> : null}
          {online && logsStatus === 'error' ? (
            <ErrorState
              title="No se pudieron leer los registros"
              detail="Entra con la cuenta de la boda e inténtalo de nuevo."
              onRetry={() => setReload((value) => value + 1)}
            />
          ) : null}
          {logsStatus === 'ready' && logs.length === 0 ? (
            <EmptyState
              title="Todavía no hay registros"
              detail="Aparecen cuando alguien hace una pregunta."
            />
          ) : null}
          {logsStatus === 'ready' && logs.length > 0 ? (
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
      ) : null}
    </div>
  );
}
