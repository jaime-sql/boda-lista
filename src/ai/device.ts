export type DeviceAvailability =
  | 'available'
  | 'downloadable'
  | 'downloading'
  | 'unavailable'
  | 'unsupported';

export async function probeDeviceModel(): Promise<DeviceAvailability> {
  const languageModel = window.LanguageModel;
  if (!languageModel || typeof languageModel.availability !== 'function') {
    return 'unsupported';
  }
  try {
    const status = await languageModel.availability();
    if (
      status === 'available' ||
      status === 'downloadable' ||
      status === 'downloading' ||
      status === 'unavailable'
    ) {
      return status;
    }
    return 'unavailable';
  } catch {
    return 'unavailable';
  }
}
