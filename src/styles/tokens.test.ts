import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import tokens from './tokens.json';

describe('design tokens', () => {
  it('ships the Izote y Barro semantic tokens', () => {
    const css = readFileSync(join(process.cwd(), 'src/styles/tokens.css'), 'utf8');
    expect(css).toContain("font-family: 'Fraunces'");
    expect(css).toContain("font-family: 'Figtree'");
    expect(css).toContain("url('./fonts/fraunces-normal-latin.woff2')");
    expect(css).toContain("url('./fonts/figtree-normal-latin.woff2')");
    expect(css).toContain('--tap-min: 48px');
    expect(css).toContain('--text-base: 1.125rem');
    expect(tokens.color.bg.value).toBe('#FBF5EC');
    expect(tokens.color.text.value).toBe('#33221C');
    expect(tokens.color['on-primary'].value).toBe('#FFFFFF');
  });

  it('keeps raw palette colors out of component styles', () => {
    for (const file of ['components.css', 'guest.css', 'app.css', 'rsvp.css', 'admin.css']) {
      const text = readFileSync(join(process.cwd(), 'src/styles', file), 'utf8');
      expect(text, file).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    }
  });
});
