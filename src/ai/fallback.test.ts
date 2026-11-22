import { describe, expect, it } from 'vitest';
import { classifyFallback, cloudModelName, DEFAULT_CLOUD_MODEL, planRoute, routeFromInference } from './fallback';

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
        deviceStatus: 'unsupported',
        inputChars: 10,
        confidence: 0.1,
        cloudCutoff: 0.6,
      }),
    ).toBeNull();
    expect(
      classifyFallback({
        route: 'cloud',
        deviceStatus: 'unavailable',
        inputChars: 10,
        confidence: null,
        cloudCutoff: 0.6,
      }),
    ).toBe('no_model');
    expect(
      classifyFallback({
        route: 'cloud',
        deviceStatus: 'available',
        inputChars: 8001,
        confidence: null,
        cloudCutoff: 0.6,
      }),
    ).toBe('long_input');
    expect(
      classifyFallback({
        route: 'cloud',
        deviceStatus: 'available',
        inputChars: 20,
        confidence: 0.2,
        cloudCutoff: 0.6,
      }),
    ).toBe('low_confidence');
    expect(
      classifyFallback({
        route: 'cloud',
        deviceStatus: 'available',
        inputChars: 20,
        confidence: 0.6,
        cloudCutoff: 0.6,
      }),
    ).toBeNull();
  });

  it('routes null thresholds online to cloud and offline to the device', () => {
    expect(
      planRoute({
        online: true,
        high: null,
        cloudCutoff: null,
        confidence: 0.99,
        inferenceSource: 'on_device',
        deviceStatus: 'available',
        inputChars: 20,
      }),
    ).toEqual({ mode: 'only_in_cloud', route: 'cloud', reason: 'no_threshold' });
    expect(
      planRoute({
        online: true,
        high: 0.85,
        cloudCutoff: null,
        confidence: 0.2,
        deviceStatus: 'available',
        inputChars: 20,
      }).reason,
    ).toBe('no_threshold');
    expect(
      planRoute({
        online: false,
        high: null,
        cloudCutoff: null,
        confidence: null,
        inferenceSource: 'in_cloud',
        deviceStatus: 'unavailable',
        inputChars: 9000,
      }),
    ).toEqual({ mode: 'only_on_device', route: 'device', reason: 'offline_no_threshold' });
  });

  it('keeps numeric thresholds, including cloud below the cutoff', () => {
    expect(
      planRoute({
        online: true,
        high: 0.85,
        cloudCutoff: 0.6,
        confidence: 0.2,
        inferenceSource: 'on_device',
        deviceStatus: 'available',
        inputChars: 20,
      }),
    ).toMatchObject({ route: 'cloud', reason: 'low_confidence' });
    expect(
      planRoute({
        online: true,
        high: 0.85,
        cloudCutoff: 0.6,
        confidence: 0.9,
        inferenceSource: 'on_device',
        deviceStatus: 'available',
        inputChars: 20,
      }),
    ).toMatchObject({ mode: 'prefer_on_device', route: 'device', reason: null });
  });

  it('defaults the cloud model name', () => {
    expect(cloudModelName('')).toBe(DEFAULT_CLOUD_MODEL);
    expect(cloudModelName('gemini-3.5-flash-lite')).toBe('gemini-3.5-flash-lite');
  });
});
