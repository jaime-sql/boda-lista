import type { Route } from '../ai/types';
import { Icon } from './Icon';

const COPY = {
  device: 'En tu teléfono',
  cloud: 'En la nube',
} as const;

type RouteBadgeProps = {
  route: Route;
};

export function RouteBadge({ route }: RouteBadgeProps) {
  return (
    <span className={`badge badge-${route === 'device' ? 'device' : 'cloud'}`} role="status">
      <Icon name={route === 'device' ? 'phone' : 'cloud'} size={18} />
      {COPY[route]}
    </span>
  );
}
