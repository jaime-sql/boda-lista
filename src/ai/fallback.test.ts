import { describe, expect, it } from 'vitest';
import { classifyFallback, cloudModelName, DEFAULT_CLOUD_MODEL, routeFromInference } from './fallback';

describe('hybrid route and fallback', () => {
  it('uses the SDK signal before the browser model', () => {
    expect(routeFromInference('on_device', 'unsupported')).toBe('device');
    expect(routeFromInference('in_cloud', 'available')).toBe('cloud');
    expect(routeFromInference(undefined, 'available')).toBe('device');
    expect(routeFromInference(undefined, 'unavailable')).toBe('cloud');
  });

  it('labels why a cloud response happened', () => {
    expect(
      classifyFallback({
        route: 'device',
        feature: 'qa',
        deviceStatus: 'unsupported',
        inputChars: 10,
        confidence: 0.1,
      }),
    ).toBeNull();
    expect(
      classifyFallback({
        route: 'cloud',
        feature: 'qa',
        deviceStatus: 'unavailable',
        inputChars: 10,
        confidence: null,
      }),
    ).toBe('no_model');
    expect(
      classifyFallback({
        route: 'cloud',
        feature: 'songs',
        deviceStatus: 'available',
        inputChars: 8001,
        confidence: null,
      }),
    ).toBe('long_input');
    expect(
      classifyFallback({
        route: 'cloud',
        feature: 'rsvp',
        deviceStatus: 'available',
        inputChars: 20,
        confidence: 0.2,
      }),
    ).toBe('low_confidence');
    expect(
      classifyFallback({
        route: 'cloud',
        feature: 'qa',
        deviceStatus: 'available',
        inputChars: 20,
        confidence: 0.6,
      }),
    ).toBeNull();
  });

  it('defaults the cloud model name', () => {
    expect(cloudModelName('')).toBe(DEFAULT_CLOUD_MODEL);
    expect(cloudModelName('gemini-3.5-flash-lite')).toBe('gemini-3.5-flash-lite');
  });
});
