import { useEffect, useMemo, useState } from 'react';
import type { Feature } from '../../ai/types';
import { Icon } from '../../components/Icon';
import { EmptyState, ErrorState, LoadingSkeleton } from '../../components/ScreenState';
import { hasThreshold, thresholdsFor } from '../../config/confidence';
import { fetchAllLogs } from '../../firebase/logs';
import {
  CLOUD_REASONS,
  buildRollup,
  isRollup,
  type CloudReason,
  type Rollup,
  type RollupCell,
} from './rollup';
import '../../styles/analytics.css';

export const SNAPSHOT_URL = '/analytics/rollup.json';
export const FEW_DATA = 'Pocos datos aún';

const FEATURE_LABEL: Record<Feature, string> = {
  guest_question: 'Preguntas de invitados',
  rsvp: 'Confirmaciones',
  song: 'Canciones',
};

const REASON_LABEL: Record<CloudReason, string> = {
  no_model: 'No había modelo en el teléfono',
  low_confidence: 'Confianza baja, bajo el umbral de cada función',
  long_input: 'El texto era muy largo',
  no_threshold: 'Aún sin umbral calibrado',
};

const FEATURES: Feature[] = ['guest_question', 'rsvp', 'song'];

type WindowKey = 'all' | 'last_24h';
type Source = 'live' | 'snapshot';
type Status = 'loading' | 'ready' | 'empty' | 'error' | 'hidden';

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}\u00a0%`;
}

export function formatLatency(ms: number): string {
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;
}

export function formatSvTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat('es-SV', {
    timeZone: 'America/El_Salvador',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date);
}

async function loadSnapshot(): Promise<Rollup | null> {
  try {
    const response = await fetch(SNAPSHOT_URL, { headers: { accept: 'application/json' } });
    if (!response.ok) return null;
    const body: unknown = await response.json();
    return isRollup(body) ? body : null;
  } catch {
    return null;
  }
}

function downloadRollup(rollup: Rollup): void {
  const blob = new Blob([`${JSON.stringify(rollup, null, 2)}\n`], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'rollup.json';
  link.click();
  URL.revokeObjectURL(url);
}

type Props = {
  signedIn: boolean;
  online: boolean;
  reload: number;
  onRetry: () => void;
};

export function AnalyticsPanel({ signedIn, online, reload, onRetry }: Props) {
  const [rollup, setRollup] = useState<Rollup | null>(null);
  const [source, setSource] = useState<Source>('live');
  const [status, setStatus] = useState<Status>('loading');
  const [liveFailed, setLiveFailed] = useState(false);
  const [windowKey, setWindowKey] = useState<WindowKey>('all');

  useEffect(() => {
    let alive = true;
    setStatus('loading');
    setLiveFailed(false);

    async function run() {
      let failed = false;
      if (signedIn && online) {
        try {
          const logs = await fetchAllLogs();
          if (!alive) return;
          setRollup(buildRollup(logs));
          setSource('live');
          setStatus(logs.length === 0 ? 'empty' : 'ready');
          return;
        } catch {
          failed = true;
        }
      }
      const snapshot = await loadSnapshot();
      if (!alive) return;
      if (snapshot) {
        setRollup(snapshot);
        setSource('snapshot');
        setLiveFailed(failed);
        setStatus(snapshot.row_count === 0 ? 'empty' : 'ready');
        return;
      }
      setRollup(null);
      if (failed) setStatus('error');
      else setStatus('hidden');
    }

    void run();
    return () => {
      alive = false;
    };
  }, [signedIn, online, reload]);

  const view = rollup?.windows[windowKey];
  const minSample = rollup?.min_sample ?? 0;

  const cloudTotal = view?.total.cloud_count ?? 0;
  const reasons = useMemo(
    () => (view ? CLOUD_REASONS.filter((reason) => view.total.fallback_reasons[reason] > 0) : []),
    [view],
  );

  if (status === 'hidden') return null;

  return (
    <section className="stack gap-3 no-print" aria-labelledby="ai-title">
      <div className="an-title-row">
        <Icon name="phone" size={22} />
        <h2 id="ai-title" className="section-title">
          Cómo responde la IA
        </h2>
      </div>
      <p className="muted sm">Cada número sale del registro real de preguntas, sin valores de ejemplo.</p>

      {status === 'loading' ? <LoadingSkeleton label="Calculando desde el registro…" /> : null}
      {status === 'error' ? (
        <ErrorState
          title="No se pudo calcular el resumen"
          detail="Entra con la cuenta de la boda e inténtalo de nuevo."
          onRetry={onRetry}
        />
      ) : null}
      {status === 'empty' ? (
        <EmptyState title="Aún no hay preguntas" detail="El resumen aparece cuando alguien usa la página de invitados." />
      ) : null}
      {liveFailed && status === 'ready' ? (
        <div className="banner banner-offline" role="status">
          <div>
            <b>No se pudo leer el registro.</b> Mostramos la última copia guardada.
          </div>
        </div>
      ) : null}

      {status === 'ready' && rollup && view ? (
        <div className="stack gap-3">
          <div className="row gap-2 an-window" role="group" aria-label="Periodo">
            <button
              type="button"
              className="chip"
              aria-pressed={windowKey === 'all'}
              onClick={() => setWindowKey('all')}
            >
              Todo
            </button>
            <button
              type="button"
              className="chip"
              aria-pressed={windowKey === 'last_24h'}
              onClick={() => setWindowKey('last_24h')}
            >
              Últimas 24 h
            </button>
          </div>

          <div className="an-tiles">
            <div className="card pad an-tile">
              <p className="muted sm">Respondido en tu teléfono</p>
              {view.total.device_share === null ? (
                <>
                  <p className="an-value an-value-small">{FEW_DATA}</p>
                  <p className="muted sm">{view.total.n} de {minSample} respuestas</p>
                </>
              ) : (
                <>
                  <p className="an-value">{formatPercent(view.total.device_share)}</p>
                  <p className="muted sm">de {view.total.n} respuestas con IA</p>
                </>
              )}
            </div>
            <div className="card pad an-tile">
              <p className="muted sm">Llamadas a la nube ahorradas</p>
              <p className="an-value">{view.total.cloud_calls_saved}</p>
              <p className="muted sm">respondidas en el teléfono por decisión, no por falta de red</p>
            </div>
            <div className="card pad an-tile">
              <p className="muted sm">Rapidez</p>
              <LatencyLine cell={view.total} />
            </div>
          </div>

          <div className="card pad stack gap-3">
            <h3 className="an-subtitle">Por función</h3>
            {FEATURES.map((feature) => (
              <FeatureBar key={feature} feature={feature} cell={view.by_feature[feature]} />
            ))}
            <p className="muted sm">
              Respondido desde la ficha: {view.total.sheet_answers}. No cuenta en los porcentajes.
            </p>
          </div>

          <div className="card pad stack gap-2">
            <h3 className="an-subtitle">Por qué pasó a la nube</h3>
            {cloudTotal === 0 ? (
              <p className="muted">Todavía ninguna respuesta fue a la nube.</p>
            ) : view.total.cloud_count < minSample ? (
              <p className="muted">{FEW_DATA}: {cloudTotal} en la nube.</p>
            ) : (
              <ul className="an-reasons">
                {reasons.map((reason) => (
                  <li key={reason}>
                    <span>{REASON_LABEL[reason]}</span>
                    <b>
                      {view.total.fallback_reasons[reason]} · {formatPercent(view.total.fallback_reasons[reason] / cloudTotal)}
                    </b>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <p className="muted sm an-footer">
            {source === 'snapshot' ? 'Copia guardada del' : 'Actualizado:'} {formatSvTime(rollup.generated_at)} (hora de
            El Salvador) · {rollup.row_count} registros
          </p>
          {source === 'live' ? (
            <button type="button" className="btn btn-secondary" onClick={() => downloadRollup(rollup)}>
              <Icon name="download" size={20} />
              Descargar rollup.json
            </button>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function LatencyLine({ cell }: { cell: RollupCell }) {
  const { device, cloud } = cell.latency_ms;
  if (device.p50 === null && cloud.p50 === null) {
    return <p className="an-value an-value-small">{FEW_DATA}</p>;
  }
  return (
    <dl className="an-speed">
      <div>
        <dt>En tu teléfono</dt>
        <dd>{device.p50 === null ? FEW_DATA : formatLatency(device.p50)}</dd>
      </div>
      <div>
        <dt>En la nube</dt>
        <dd>{cloud.p50 === null ? FEW_DATA : formatLatency(cloud.p50)}</dd>
      </div>
    </dl>
  );
}

function FeatureBar({ feature, cell }: { feature: Feature; cell: RollupCell }) {
  const total = cell.device_count + cell.cloud_count + cell.offline_no_threshold;
  const noThreshold = !hasThreshold(thresholdsFor(feature));
  const pct = (count: number) => `${(count / total) * 100}%`;
  return (
    <div className="stack gap-1">
      <div className="an-feature-head">
        <b>{FEATURE_LABEL[feature]}</b>
        {noThreshold ? <span className="badge badge-pending">Sin umbral aún</span> : null}
      </div>
      {total === 0 ? (
        <p className="muted sm">Sin respuestas con IA en este periodo.</p>
      ) : (
        <>
          <div
            className="an-bar"
            role="img"
            aria-label={`${FEATURE_LABEL[feature]}: ${cell.device_count} en tu teléfono, ${cell.cloud_count} en la nube, ${cell.offline_no_threshold} sin conexión y sin umbral`}
          >
            {cell.device_count > 0 ? <span className="an-seg an-seg-device" style={{ width: pct(cell.device_count) }} /> : null}
            {cell.cloud_count > 0 ? <span className="an-seg an-seg-cloud" style={{ width: pct(cell.cloud_count) }} /> : null}
            {cell.offline_no_threshold > 0 ? (
              <span className="an-seg an-seg-offline" style={{ width: pct(cell.offline_no_threshold) }} />
            ) : null}
          </div>
          <ul className="an-legend">
            <li>
              <span className="badge badge-device">En tu teléfono</span> {cell.device_count}
              {cell.device_share === null ? null : ` · ${formatPercent(cell.device_share)}`}
            </li>
            <li>
              <span className="badge badge-cloud">En la nube</span> {cell.cloud_count}
            </li>
            {cell.offline_no_threshold > 0 ? (
              <li>
                <span className="badge badge-offline">Sin conexión, sin umbral</span> {cell.offline_no_threshold}
              </li>
            ) : null}
          </ul>
          {cell.device_share === null ? <p className="muted sm">{FEW_DATA}: no se muestra porcentaje.</p> : null}
        </>
      )}
    </div>
  );
}
