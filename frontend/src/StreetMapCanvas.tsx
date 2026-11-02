import {useEffect, useRef, useState} from 'react';
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
  const [partial,setPartial]=useState(false);
  const callbacks=useRef({onSelect,onFailure,labelStatus}); callbacks.current={onSelect,onFailure,labelStatus};
  const tx=(en:string,ar:string)=>lang==='ar'?ar:en;
  useEffect(() => {
    if (!container.current || !pins.length || !streetTileProvider) return;
    const map=L.map(container.current,{zoomControl:false,scrollWheelZoom:false,zoomAnimation:false,fadeAnimation:false,markerZoomAnimation:false,minZoom:2,maxZoom:19});
    instance.current=map;
    L.control.zoom({zoomInTitle:lang==='ar'?'تكبير':'Zoom in',zoomOutTitle:lang==='ar'?'تصغير':'Zoom out'}).addTo(map);
    map.attributionControl.setPrefix(false);
    const tiles=L.tileLayer(streetTileProvider.url,OSM_TILE_OPTIONS);
    let stopped=false, settled=false, timedOut=false, deadline:number|undefined;
    // Failed tiles by coordinates. Leaflet never re-requests an errored tile, so a later load cycle
    // (resize, pan) must not forget it; it is cleared only when the tile reloads or is removed.
    const failedTiles=new Map<string,HTMLElement>();
    const tileKey=(c:L.Coords)=>`${c.x}:${c.y}:${c.z}`;
    function fail(){if(!stopped){stopped=true;callbacks.current.onFailure();}}
    function inView(el:Element){
      const view=container.current?.getBoundingClientRect(), rect=el.getBoundingClientRect();
      return Boolean(view&&rect.width>0&&rect.height>0&&rect.right>view.left&&rect.left<view.right&&rect.bottom>view.top&&rect.top<view.bottom);
    }
    // Decide after the current load settles, not on the first individual tile error.
    // Include cached visible tiles when panning; offscreen tiles cannot mask an empty view.
    function hasVisibleTile(){
      return Boolean(container.current&&Array.from(container.current.querySelectorAll('.leaflet-tile-loaded')).some(inView));
    }
    // Still-loading tiles are never recorded; stale zoom layers and offscreen tiles do not count.
    function hasVisibleFailure(){
      const zoom=map.getZoom();
      return Array.from(failedTiles).some(([key,el])=>el.isConnected&&Number(key.split(':')[2])===zoom&&!el.classList.contains('leaflet-tile-loaded')&&inView(el));
    }
    function settle(){
      if(stopped)return;
      settled=true;
      if(!hasVisibleTile())fail();
      else setPartial(timedOut||hasVisibleFailure());
    }
    tiles.on('loading',()=>{
      window.clearTimeout(deadline);
      deadline=window.setTimeout(()=>{timedOut=true;settle();},15000);
    });
    tiles.on('tileerror',event=>failedTiles.set(tileKey(event.coords),event.tile));
    tiles.on('tileload',event=>failedTiles.delete(tileKey(event.coords)));
    tiles.on('tileunload',event=>failedTiles.delete(tileKey(event.coords)));
    tiles.on('load',()=>{window.clearTimeout(deadline);timedOut=false;settle();});
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
    // A move that needs no new tiles fires no load event; refresh only the partial notice so a failure
    // that left the view clears. Total failure is decided only at a load or timeout: on a far pan this
    // handler can run after old tiles are pruned but before GridLayer schedules the new ones.
    map.on('moveend',()=>{if(settled&&!stopped&&!tiles.isLoading())setPartial(timedOut||hasVisibleFailure());});
    const resize=new ResizeObserver(()=>map.invalidateSize({pan:false}));resize.observe(container.current);
    return()=>{stopped=true;window.clearTimeout(deadline);resize.disconnect();tiles.off();map.remove();markers.current.clear();instance.current=null;};
  },[pins,lang,simulated]);
  useEffect(()=>{
    for(const [id,marker] of markers.current)marker.getElement()?.classList.toggle('street-pin-selected',id===selectedId);
    const marker=markers.current.get(selectedId);
    if(marker && instance.current && !instance.current.getBounds().contains(marker.getLatLng()))instance.current.panTo(marker.getLatLng(),{animate:false});
  },[selectedId,pins,lang]);
  return <><div ref={container} className="street-map-canvas" dir="ltr" aria-label={tx('Street map: use arrow keys to pan, plus and minus to zoom. Choose a pin or use the report selector below.','خريطة الشوارع: استخدم الأسهم للتحريك وزرّي الجمع والطرح للتكبير والتصغير. اختر نقطة أو استخدم قائمة البلاغات أدناه.')}/>{partial&&<p className="street-map-partial" role="status">{tx('Some street tiles did not load. Pins remain available, but the background is incomplete. Turn the street map off and load it again to retry, or use the coordinate diagram.','لم تُحمّل بعض أجزاء خريطة الشوارع. النقاط متاحة، لكن الخلفية غير مكتملة. أوقف خريطة الشوارع وحمّلها مجددًا للمحاولة، أو استخدم مخطط الإحداثيات.')}</p>}</>;
}
