import {useEffect, useRef} from 'react';
import * as L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {OSM_TILE_OPTIONS, pinStatusColor} from './streetMap';
import {streetTileProvider} from './streetTileProvider';
import type {StreetPin} from './streetMap';

type Props = {
  pins:StreetPin[]; lang:string; simulated:boolean; selectedId:string;
  labelStatus:(status:string)=>string; onSelect:(id:string)=>void; onFailure:()=>void;
};

/** Loaded from the local bundle only after opt-in. Never puts report text into HTML strings. */
export default function StreetMapCanvas({pins, lang, simulated, selectedId, labelStatus, onSelect, onFailure}:Props) {
  const container=useRef<HTMLDivElement>(null), instance=useRef<L.Map|null>(null);
  const markers=useRef(new Map<string,L.Marker>());
  const callbacks=useRef({onSelect,onFailure,labelStatus}); callbacks.current={onSelect,onFailure,labelStatus};
  const tx=(en:string,ar:string)=>lang==='ar'?ar:en;
  useEffect(() => {
    if (!container.current || !pins.length || !streetTileProvider) return;
    const map=L.map(container.current,{zoomControl:false,scrollWheelZoom:false,zoomAnimation:false,fadeAnimation:false,markerZoomAnimation:false,minZoom:2,maxZoom:19});
    instance.current=map;
    L.control.zoom({zoomInTitle:lang==='ar'?'تكبير':'Zoom in',zoomOutTitle:lang==='ar'?'تصغير':'Zoom out'}).addTo(map);
    map.attributionControl.setPrefix(false);
    const tiles=L.tileLayer(streetTileProvider.url,OSM_TILE_OPTIONS);
    let stopped=false, loaded=false;
    function fail(){if(!stopped){stopped=true;callbacks.current.onFailure();}}
    tiles.on('tileerror',fail);
    tiles.on('tileload',()=>{loaded=true;});
    const deadline=window.setTimeout(()=>{if(!loaded)fail();},15000);
    // Fit observed coordinates only. No default city or inferred location is introduced.
    map.fitBounds(L.latLngBounds(pins.map(pin=>[pin.latitude!,pin.longitude!] as L.LatLngTuple)),{padding:[35,35],maxZoom:16,animate:false});
    for (const [index,pin] of pins.entries()) {
      const icon=document.createElement('span');icon.textContent=String(index+1);
      icon.className='street-pin-number';icon.style.backgroundColor=pinStatusColor(pin.status);
      const title=`${lang==='ar'?'بلاغ':'Report'} ${pin.id} · ${callbacks.current.labelStatus(pin.status)}${simulated?(lang==='ar'?' · محاكاة':' · Simulated'):''}`;
      const marker=L.marker([pin.latitude!,pin.longitude!],{icon:L.divIcon({html:icon,className:`street-pin${simulated?' street-pin-simulated':''}`,iconSize:[36,36],iconAnchor:[18,18]}),title,alt:title,keyboard:true});
      marker.on('click',()=>callbacks.current.onSelect(pin.id));marker.addTo(map);markers.current.set(pin.id,marker);
      const element=marker.getElement();element?.setAttribute('aria-label',title);
      const activate=(event:KeyboardEvent)=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();event.stopPropagation();callbacks.current.onSelect(pin.id);}};
      element?.addEventListener('keydown',activate);
      marker.on('remove',()=>element?.removeEventListener('keydown',activate));
    }
    tiles.addTo(map);
    const resize=new ResizeObserver(()=>map.invalidateSize({pan:false}));resize.observe(container.current);
    return()=>{stopped=true;window.clearTimeout(deadline);resize.disconnect();tiles.off();map.remove();markers.current.clear();instance.current=null;};
  },[pins,lang,simulated]);
  useEffect(()=>{
    for(const [id,marker] of markers.current)marker.getElement()?.classList.toggle('street-pin-selected',id===selectedId);
    const marker=markers.current.get(selectedId);
    if(marker && instance.current && !instance.current.getBounds().contains(marker.getLatLng()))instance.current.panTo(marker.getLatLng(),{animate:false});
  },[selectedId,pins,lang]);
  return <div ref={container} className="street-map-canvas" dir="ltr" aria-label={tx('Street map: use arrow keys to pan, plus and minus to zoom. Choose a pin or use the report selector below.','خريطة الشوارع: استخدم الأسهم للتحريك وزرّي الجمع والطرح للتكبير والتصغير. اختر نقطة أو استخدم قائمة البلاغات أدناه.')}/>;
}
