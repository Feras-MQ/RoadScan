// Display labels only: checkpoint filenames, IDs and metric provenance stay intact.
export function modelName(name: string, inputSize?: number) {
  const yolo = name.match(/(?:^|[^a-z0-9])yolo(?:v)?(\d+)([nsmlx])(?=$|[^a-z0-9])/i);
  const detr = name.match(/rt[-_ ]?detr[-_ ]?([lx])(?=$|[^a-z0-9])/i);
  const family = yolo ? `YOLO${Number(yolo[1]) <= 10 ? 'v' : ''}${yolo[1]}${yolo[2].toLowerCase()}` : detr ? `RT-DETR ${detr[1].toUpperCase()}` : null;
  if (!family) return name.replace(/_/g, ' ');
  const size = name.match(/(?:^|_)(\d{3,4})(?:px)?(?=_|\.|$|@)/i)?.[1] || inputSize;
  const experiment = /^main_/i.test(name) ? 'Main' : /clean_labels/i.test(name) ? 'Cleaned labels' : /no_augmentation/i.test(name) ? 'No augmentation' : /vertical_flip/i.test(name) ? 'Vertical flip' : /without_India/i.test(name) ? 'India held out' : /^e2_/i.test(name) ? 'Size experiment' : null;
  const epoch = name.match(/epoch0*(\d+)/i)?.[1];
  return [family, experiment, /RDD2022/i.test(name) ? 'RDD2022' : /baseline/i.test(name) ? 'Baseline' : null,
    size ? `${size} px` : null, epoch ? `Epoch ${epoch}` : null].filter(Boolean).join(' · ');
}
