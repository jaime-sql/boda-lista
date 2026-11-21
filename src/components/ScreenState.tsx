type LoadingSkeletonProps = {
  label: string;
};

export function LoadingSkeleton({ label }: LoadingSkeletonProps) {
  return (
    <div className="card pad" role="status" aria-live="polite">
      <p className="muted">{label}</p>
      <div className="row gap-3">
        <span className="typing" aria-hidden="true">
          <b />
          <b />
          <b />
        </span>
      </div>
    </div>
  );
}

type EmptyStateProps = {
  title: string;
  detail: string;
};

export function EmptyState({ title, detail }: EmptyStateProps) {
  return (
    <div className="card pad stack gap-2">
      <h2 className="section-title">{title}</h2>
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
    <div className="card pad stack gap-3" role="alert">
      <h2 className="section-title">{title}</h2>
      <p>{detail}</p>
      <button type="button" className="btn btn-primary" onClick={onRetry}>
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
    <div className="banner banner-offline" role="status">
      <div>
        <b>Sin conexión.</b> {detail}
      </div>
    </div>
  );
}
