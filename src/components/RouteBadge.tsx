import type { Route } from '../ai/types';

const COPY: Record<Route, string> = {
  device: 'En tu teléfono',
  cloud: 'En la nube',
};

type RouteBadgeProps = {
  route: Route;
};

export function RouteBadge({ route }: RouteBadgeProps) {
  return (
    <span className={`badge badge-${route}`} role="status">
      {COPY[route]}
    </span>
  );
}
