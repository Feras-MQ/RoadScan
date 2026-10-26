export const motionQuery = '(prefers-reduced-motion: reduce)';

export function motionEnabled(override: boolean | null, systemReduced: boolean) {
  return override ?? !systemReduced;
}

export function subscribeMotion(callback: () => void) {
  const preference = window.matchMedia(motionQuery);
  preference.addEventListener('change', callback);
  return () => preference.removeEventListener('change', callback);
}
