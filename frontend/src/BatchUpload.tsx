import type {BatchItem} from './batchUpload';
import './batchUpload.css';

type Props = {items: BatchItem[]; lang: string; busy: boolean; connected: boolean; maxMb: number; start: (retry?: boolean) => void; clear: () => void; open: (id: string) => void; review: () => void};

export default function BatchUpload({items, lang, busy, connected, maxMb, start, clear, open, review}: Props) {
  const tx = (en: string, ar: string) => lang === 'ar' ? ar : en;
  const saved = items.filter(item => item.status === 'saved').length;
  const failed = items.some(item => item.status === 'failed');
  const unconfirmed = items.some(item => item.status === 'unconfirmed');
  const queued = items.filter(item => item.status === 'queued').length;
  const labels = {queued: tx('Waiting', 'بانتظار الرفع'), uploading: tx('Analyzing…', 'جارٍ التحليل…'), saved: tx('Saved', 'تم الحفظ'), failed: tx('Request rejected', 'رُفض الطلب'), unconfirmed: tx('Save not confirmed — check Review before retrying', 'الحفظ غير مؤكد — تحقق من المراجعة قبل إعادة المحاولة'), rejected: tx('Not supported', 'ملف غير صالح')};
  return <section className="batch-upload" aria-label={tx('Photo batch', 'مجموعة الصور')}>
    <h3>{tx('Photo batch', 'مجموعة الصور')} · {items.length}</h3>
    <p>{tx('One report per photo, processed one at a time. Batch photos have no location; upload individually to add coordinates.', 'بلاغ مستقل لكل صورة، وتُعالج الصور بالتتابع. تُحفظ صور المجموعة دون موقع؛ ارفع الصورة منفردة لإضافة الإحداثيات.')}</p>
    <p role="status" aria-live="polite">{saved} / {items.length} {tx('saved', 'محفوظة')} · {queued} {tx('waiting', 'بانتظار الرفع')}</p>
    <progress max={items.length} value={items.filter(item => !['queued', 'uploading'].includes(item.status)).length} aria-label={tx('Batch progress', 'تقدم المجموعة')}/>
    <ol>{items.map((item, index) => <li key={index}>
      <div><strong dir="auto">{item.file.name}</strong><span>{labels[item.status]}</span></div>
      {item.error && <small className="batch-error">{item.error === 'unsupported' ? tx('Choose JPEG, PNG or WebP.', 'اختر JPEG أو PNG أو WebP.') : item.error === 'too-large' ? tx(`File exceeds ${maxMb} MB.`, `يتجاوز الملف ${maxMb} ميجابايت.`) : item.error}</small>}
      {item.id && <button disabled={busy} onClick={() => open(item.id!)}>{tx('Open report', 'فتح البلاغ')}</button>}
    </li>)}</ol>
    {unconfirmed && <p>{tx('Unconfirmed photos are excluded from retries: they may already be saved. Check the review queue; only if missing, clear this selection and select that photo again.', 'الصور غير المؤكدة مستثناة من إعادة المحاولة لأنها قد تكون محفوظة. تحقق من قائمة المراجعة؛ وإذا لم تجد البلاغ، امسح هذا الاختيار واختر تلك الصورة مجدداً.')}</p>}
    <div className="batch-actions">
      {queued > 0 && <button className="primary" disabled={busy || !connected} onClick={() => start()}>{saved || failed || unconfirmed ? tx('Continue remaining', 'متابعة الصور المتبقية') : tx('Analyze photo batch', 'تحليل مجموعة الصور')}</button>}
      {failed && <button disabled={busy || !connected} onClick={() => start(true)}>{queued ? tx('Retry rejected & continue', 'إعادة المرفوضة ومتابعة المتبقية') : tx('Retry rejected photos', 'إعادة محاولة الصور المرفوضة')}</button>}
      {unconfirmed && <button disabled={busy || !connected} onClick={review}>{tx('Check review queue', 'تحقق من قائمة المراجعة')}</button>}
      <button disabled={busy} onClick={clear}>{tx('Clear selection', 'مسح الاختيار')}</button>
    </div>
    <small>{tx('Clearing removes this selection only; saved reports stay in the review queue.', 'المسح يزيل هذا الاختيار فقط؛ تبقى البلاغات المحفوظة في قائمة المراجعة.')}</small>
  </section>;
}
