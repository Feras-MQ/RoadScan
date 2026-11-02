import {useEffect, useState} from 'react';
import {readPinResult,streetPinsPath} from './streetMap';
import EvidenceMap from './EvidenceMap';
import type {EvidenceReport} from './EvidenceMap';
import {mapRequestPath, readLocationCounts} from './reportMap';
import type {LocationGroup} from './reportMap';

type Props = {
  lang:string; connected:boolean; busy:boolean; sessionKey:string;
  stats:{total:number; by_location?:unknown}|null;
  request:(path:string, options?:RequestInit)=>Promise<any>;
  labelStatus:(status:string)=>string; onOpen:(id:string)=>void; onNewInspection:()=>void; onHelp:()=>void;
};

/** Map browsing owns its page/filters; Review queue state is never changed here. */
export default function MapWorkspace({lang, connected, busy, sessionKey, stats, request, ...actions}:Props) {
  const [page, setPage] = useState(1), [group, setGroup] = useState<LocationGroup>('recorded');
  const [status, setStatus] = useState(''), [search, setSearch] = useState(''), [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{key:string; items:EvidenceReport[]; total:number}|null>(null);
  const [loading, setLoading] = useState(false), [error, setError] = useState('');
  const [pinVersion,setPinVersion]=useState(0);
  useEffect(()=>setPinVersion(version=>version+1),[stats]);
  const coverage = readLocationCounts(stats?.by_location, stats?.total);
  const path = mapRequestPath(page, group, status, search, Boolean(coverage));
  useEffect(() => {
    const controller = new AbortController();
    setResult(null); setError(''); setLoading(connected);
    if (connected) request(path, {signal:controller.signal}).then(data => {
      if (controller.signal.aborted) return;
      const lastPage = Math.max(1, Math.ceil(data.total / 20));
      if (page > lastPage) {setPage(lastPage); return;}
      setResult({key:path, items:data.items, total:data.total});
    }).catch(reason => {if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : String(reason));})
      .finally(() => {if (!controller.signal.aborted) setLoading(false);});
    return () => controller.abort();
  }, [connected, path, page, request, stats, retry]);
  const current = connected && result?.key === path ? result : null;
  const tx = (en:string, ar:string) => lang === 'ar' ? ar : en;
  return <>
    {error && <div className="alert error" role="alert"><span>{tx('Could not load map reports. ', 'تعذر تحميل بلاغات الخريطة. ')}{error}</span><button disabled={loading} onClick={() => setRetry(value => value + 1)}>{tx('Retry map', 'إعادة تحميل الخريطة')}</button></div>}
    <EvidenceMap {...actions} lang={lang} connected={connected} busy={busy || loading || (connected && !current && !error)} sessionKey={sessionKey}
      pinQueryKey={`${group}|${status}|${pinVersion}`}
      loadPins={async(damage,signal)=>{
        const pinPath=streetPinsPath(group,status,damage);
        if(!pinPath||search)throw Error('Street pins are unavailable for this view');
        const value=readPinResult(await request(pinPath,{signal}),group);
        if(!value)throw Error('Invalid street pin response');
        return value;
      }}
      loadFailed={Boolean(error)}
      reports={current?.items || []} total={current?.total || 0} page={page} group={group} coverage={coverage}
      statusFilter={status} searchQuery={search} onPage={setPage}
      onGroup={next => {setGroup(next); if (coverage) setPage(1);}}
      onFilters={(nextStatus, nextSearch) => {setStatus(nextStatus); setSearch(nextSearch); setPage(1);}}/>
  </>;
}
