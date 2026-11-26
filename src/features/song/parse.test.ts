import { describe, expect, it } from 'vitest';
import { thresholdsFor } from '../../config/confidence';
import { parseSongOutput } from './parse';

const valid = {
  title: 'Vivir Mi Vida',
  artist: 'Marc Anthony',
  energy: 'dance',
  ambiguous: false,
  confidence: 0.92,
};

describe('song parsing', () => {
  it('accepts schema-shaped JSON and strips markdown fences', () => {
    expect(parseSongOutput(JSON.stringify(valid))).toEqual(valid);
    expect(parseSongOutput('```json\n' + JSON.stringify(valid) + '\n```')?.title).toBe('Vivir Mi Vida');
  });

  it('normalizes whitespace and allows null artist or energy on clear songs', () => {
    const parsed = parseSongOutput(
      JSON.stringify({
        title: '  Bésame mucho ',
        artist: '  ',
        energy: null,
        ambiguous: false,
        confidence: 0.7,
      }),
    );
    expect(parsed).toEqual({
      title: 'Bésame mucho',
      artist: null,
      energy: null,
      ambiguous: false,
      confidence: 0.7,
    });
  });

  it('enforces ambiguous requests having title === null', () => {
    expect(
      parseSongOutput(
        JSON.stringify({
          title: null,
          artist: 'Marc Anthony',
          energy: 'dance',
          ambiguous: true,
          confidence: 0.4,
        }),
      ),
    ).toMatchObject({ title: null, artist: 'Marc Anthony', ambiguous: true });

    expect(
      parseSongOutput(
        JSON.stringify({
          title: 'Vivir Mi Vida',
          artist: 'Marc Anthony',
          energy: 'dance',
          ambiguous: true,
          confidence: 0.4,
        }),
      ),
    ).toBeNull();
  });

  it('rejects non-ambiguous responses missing a title, invalid energy, or bad confidence', () => {
    expect(parseSongOutput('no es json')).toBeNull();
    expect(parseSongOutput('[]')).toBeNull();
    expect(parseSongOutput(JSON.stringify({ ...valid, title: null, ambiguous: false }))).toBeNull();
    expect(parseSongOutput(JSON.stringify({ ...valid, title: '   ', ambiguous: false }))).toBeNull();
    expect(parseSongOutput(JSON.stringify({ ...valid, energy: 'fast' }))).toBeNull();
    expect(parseSongOutput(JSON.stringify({ ...valid, ambiguous: 'yes' }))).toBeNull();
    expect(parseSongOutput(JSON.stringify({ ...valid, confidence: 1.5 }))).toBeNull();
    expect(parseSongOutput(JSON.stringify({ ...valid, confidence: -0.1 }))).toBeNull();
  });

  it('uses the canonical song threshold key', () => {
    expect(thresholdsFor('song').min_n).toBe(20);
  });
});
