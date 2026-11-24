import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { RouteBadge } from './RouteBadge';

describe('RouteBadge', () => {
  it('names the real route in Spanish', () => {
    expect(renderToStaticMarkup(<RouteBadge route="device" />)).toContain('En tu teléfono');
    expect(renderToStaticMarkup(<RouteBadge route="cloud" />)).toContain('En la nube');
    expect(renderToStaticMarkup(<RouteBadge route="sheet" />)).toContain('En la hoja');
    expect(renderToStaticMarkup(<RouteBadge route="sheet" />)).not.toContain('En la nube');
  });
});
