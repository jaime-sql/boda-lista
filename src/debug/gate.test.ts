import { describe, expect, it } from 'vitest';
import { isDebugPanelEnabled } from './gate';

describe('debug panel gate', () => {
  it('stays off in production even with the query', () => {
    expect(isDebugPanelEnabled({ DEV: false }, '?debug=1')).toBe(false);
    expect(isDebugPanelEnabled({ DEV: false, VITE_ENABLE_DEBUG: 'false' }, '?debug=1')).toBe(false);
    expect(isDebugPanelEnabled({ DEV: false, VITE_ENABLE_DEBUG: '' }, '?debug=1')).toBe(false);
  });

  it('turns on for preview builds and dev builds only with ?debug=1', () => {
    expect(isDebugPanelEnabled({ DEV: false, VITE_ENABLE_DEBUG: 'true' }, '?debug=1')).toBe(true);
    expect(isDebugPanelEnabled({ DEV: true }, '?debug=1')).toBe(true);
    expect(isDebugPanelEnabled({ DEV: false, VITE_ENABLE_DEBUG: 'true' }, '')).toBe(false);
    expect(isDebugPanelEnabled({ DEV: true }, '?debug=0')).toBe(false);
  });
});
