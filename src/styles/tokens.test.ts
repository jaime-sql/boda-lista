import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import tokens from './tokens.json';

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });
}

function luminance(hex: string): number {
  const normalized = hex.slice(1);
  const channels = [0, 2, 4].map((index) => {
    const value = parseInt(normalized.slice(index, index + 2), 16) / 255;
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrast(a: string, b: string): number {
  const lighter = Math.max(luminance(a), luminance(b));
  const darker = Math.min(luminance(a), luminance(b));
  return (lighter + 0.05) / (darker + 0.05);
}

describe('design tokens', () => {
  it('matches tokens.css and keeps accessible floors', () => {
    const css = readFileSync(join(process.cwd(), 'src/styles/tokens.css'), 'utf8').replace(
      /\/\*[\s\S]*?\*\//g,
      '',
    );
    const declared = new Map<string, string>();
    for (const match of css.matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/g)) {
      declared.set(match[1], match[2].trim());
    }
    expect(Object.fromEntries(declared)).toEqual(tokens);
    expect(parseFloat(tokens['--font-size-body'])).toBeGreaterThanOrEqual(18);
    expect(parseFloat(tokens['--size-tap'])).toBeGreaterThanOrEqual(48);
  });

  it('keeps text contrast at WCAG AA', () => {
    const tokenMap: Record<string, string> = tokens;
    const pairs: Array<[string, string]> = [
      ['--color-text', '--color-bg'],
      ['--color-text', '--color-surface'],
      ['--color-text-muted', '--color-bg'],
      ['--color-text-muted', '--color-surface'],
      ['--color-button-text', '--color-button-bg'],
      ['--color-button-disabled-text', '--color-button-disabled-bg'],
      ['--color-danger', '--color-surface'],
      ['--color-danger', '--color-bg'],
      ['--color-badge-device-text', '--color-badge-device-bg'],
      ['--color-badge-cloud-text', '--color-badge-cloud-bg'],
      ['--color-link', '--color-bg'],
    ];
    for (const [ink, paper] of pairs) {
      expect(contrast(tokenMap[ink], tokenMap[paper]), `${ink} on ${paper}`).toBeGreaterThanOrEqual(4.5);
    }
  });

  it('keeps raw colors and sizes inside the token files', () => {
    const files = walk(join(process.cwd(), 'src')).filter(
      (file) =>
        (file.endsWith('.css') || file.endsWith('.tsx')) &&
        !file.endsWith('tokens.css') &&
        !file.endsWith('.test.tsx'),
    );
    for (const file of files) {
      const text = readFileSync(file, 'utf8');
      expect(text, file).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
      expect(text, file).not.toMatch(/\d+px/);
      expect(text, file).not.toMatch(/style=\{|style="/);
    }
    const motion = readFileSync(join(process.cwd(), 'src/styles/global.css'), 'utf8');
    expect(motion).toContain('prefers-reduced-motion');
  });
});
