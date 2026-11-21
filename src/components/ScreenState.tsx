export const THINKING_LABEL = 'pensando en tu teléfono...';

type LoadingSkeletonProps = {
  label: string;
};

export function LoadingSkeleton({ label }: LoadingSkeletonProps) {
  return (
    <div className="state" role="status" aria-live="polite">
      <p className="muted">{label}</p>
      <div className="skeleton" aria-hidden="true" />
      <div className="skeleton skeleton-short" aria-hidden="true" />
    </div>
  );
}

type EmptyStateProps = {
  title: string;
  detail: string;
};

export function EmptyState({ title, detail }: EmptyStateProps) {
  return (
    <div className="state">
      <h2 className="heading">{title}</h2>
      <p className="muted">{detail}</p>
    </div>
  );
}

type ErrorStateProps = {
  title: string;
  detail: string;
  onRetry: () => void;
};

export function ErrorState({ title, detail, onRetry }: ErrorStateProps) {
  return (
    <div className="state" role="alert">
      <h2 className="heading state-error">{title}</h2>
      <p>{detail}</p>
      <button type="button" className="button" onClick={onRetry}>
        Reintentar
      </button>
    </div>
  );
}

type OfflineStateProps = {
  detail: string;
};

export function OfflineState({ detail }: OfflineStateProps) {
  return (
    <div className="state" role="status">
      <h2 className="heading">Sin conexión</h2>
      <p>{detail}</p>
    </div>
  );
}
