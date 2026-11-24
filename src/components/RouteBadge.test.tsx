import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { RouteBadge } from './RouteBadge';

describe('RouteBadge', () => {
  it('names the real route in Spanish', () => {
    expect(renderToStaticMarkup(<RouteBadge route="device" />)).toContain('En tu teléfono');
    expect(renderToStaticMarkup(<RouteBadge route="cloud" />)).toContain('En la nube');
    const sheet = renderToStaticMarkup(<RouteBadge route="sheet" />);
    expect(sheet).toContain('De la ficha de la boda');
    expect(sheet).toContain('badge-sheet');
    expect(sheet).not.toContain('En la nube');
    expect(sheet).not.toContain('En tu teléfono');
  });

  it('names a sheet answer in English when the page locale is English', () => {
    const sheet = renderToStaticMarkup(<RouteBadge route="sheet" lang="en" />);
    expect(sheet).toContain('From the wedding info');
    expect(sheet).toContain('badge-sheet');
    expect(sheet).not.toContain('De la ficha de la boda');
  });
});
