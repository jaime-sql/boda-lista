import type { Route } from '../ai/types';
import { Icon, type IconName } from './Icon';

const COPY: Record<Route, { label: string; icon: IconName; badge: string }> = {
  device: { label: 'En tu teléfono', icon: 'phone', badge: 'badge-device' },
  cloud: { label: 'En la nube', icon: 'cloud', badge: 'badge-cloud' },
  sheet: { label: 'En la hoja', icon: 'info', badge: 'badge-sheet' },
};

type RouteBadgeProps = {
  route: Route;
};

export function RouteBadge({ route }: RouteBadgeProps) {
  const copy = COPY[route];
  return (
    <span className={`badge ${copy.badge}`} role="status">
      <Icon name={copy.icon} size={18} />
      {copy.label}
    </span>
  );
}
