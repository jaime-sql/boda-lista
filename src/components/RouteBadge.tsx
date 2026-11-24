import type { Route } from '../ai/types';
import { Icon, type IconName } from './Icon';

const COPY: Record<Exclude<Route, 'sheet'>, { label: string; icon: IconName; badge: string }> = {
  device: { label: 'En tu teléfono', icon: 'phone', badge: 'badge-device' },
  cloud: { label: 'En la nube', icon: 'cloud', badge: 'badge-cloud' },
};

const SHEET_LABEL = {
  es: 'De la ficha de la boda',
  en: 'From the wedding info',
} as const;

type RouteBadgeProps = {
  route: Route;
  lang?: 'es' | 'en';
};

export function RouteBadge({ route, lang = 'es' }: RouteBadgeProps) {
  const copy =
    route === 'sheet'
      ? { label: SHEET_LABEL[lang], icon: 'info' as const, badge: 'badge-sheet' }
      : COPY[route];
  return (
    <span className={`badge ${copy.badge}`} role="status">
      <Icon name={copy.icon} size={18} />
      {copy.label}
    </span>
  );
}
