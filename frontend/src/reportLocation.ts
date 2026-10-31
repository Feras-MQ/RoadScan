export function googleMapsUrl(latitude?: number | null, longitude?: number | null) {
  if (typeof latitude !== 'number' || typeof longitude !== 'number' ||
      !Number.isFinite(latitude) || !Number.isFinite(longitude) ||
      Math.abs(latitude) > 90 || Math.abs(longitude) > 180) return null;
  return 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(`${latitude},${longitude}`);
}

export function locationSourceLabel(source:string|undefined,lang:string) {
  const labels:Record<string,[string,string]>={manual:['Manually entered','أُدخل يدويًا'],device_gps:['Device GPS (reported)','GPS الجهاز (حسب المصدر)'],simulated:['Simulated location','موقع محاكاة'],not_provided:['Not provided','غير متوفر']};
  return (labels[source||'']||['Source unspecified','المصدر غير محدد'])[lang==='ar'?1:0];
}

export function recordedMapUrl(report?:{latitude?:number|null;longitude?:number|null;location_source?:string}|null) {
  return report&&['manual','device_gps'].includes(report.location_source||'')?googleMapsUrl(report.latitude,report.longitude):null;
}
