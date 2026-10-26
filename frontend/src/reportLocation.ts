export function googleMapsUrl(latitude?: number | null, longitude?: number | null) {
  if (typeof latitude !== 'number' || typeof longitude !== 'number' ||
      !Number.isFinite(latitude) || !Number.isFinite(longitude) ||
      Math.abs(latitude) > 90 || Math.abs(longitude) > 180) return null;
  return 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(`${latitude},${longitude}`);
}
