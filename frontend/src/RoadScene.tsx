import {useId} from 'react';
import {Pause, Play} from 'lucide-react';
import './RoadScene.css';

export default function RoadScene({lang, playing, onToggle}: {lang: string; playing: boolean; onToggle: () => void}) {
  const id = useId().replaceAll(':', '');
  const tx = (en: string, ar: string) => lang === 'ar' ? ar : en;
  return <figure className={'road-scene'+(playing?' is-playing':' is-paused')} aria-labelledby={id+'-caption'}>
    <svg className="road-scene-art" viewBox="0 0 920 600" fill="none" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id={id+'-ground'} x1="160" y1="140" x2="750" y2="570" gradientUnits="userSpaceOnUse"><stop stopColor="#21343b"/><stop offset="1" stopColor="#080f15"/></linearGradient>
        <linearGradient id={id+'-road'} x1="220" y1="510" x2="710" y2="160" gradientUnits="userSpaceOnUse"><stop stopColor="#24343d"/><stop offset=".55" stopColor="#101d26"/><stop offset="1" stopColor="#2b414a"/></linearGradient>
        <linearGradient id={id+'-edge'}><stop stopColor="#75e5f5" stopOpacity=".08"/><stop offset=".48" stopColor="#75e5f5"/><stop offset="1" stopColor="#d8f561" stopOpacity=".2"/></linearGradient>
        <linearGradient id={id+'-beam'} x1="280" y1="500" x2="315" y2="455" gradientUnits="userSpaceOnUse"><stop stopColor="#d8f561" stopOpacity="0"/><stop offset=".82" stopColor="#d8f561" stopOpacity=".08"/><stop offset="1" stopColor="#d8f561" stopOpacity=".8"/></linearGradient>
        <radialGradient id={id+'-halo'}><stop stopColor="#75e5f5" stopOpacity=".19"/><stop offset="1" stopColor="#75e5f5" stopOpacity="0"/></radialGradient>
        <pattern id={id+'-grid'} width="32" height="32" patternUnits="userSpaceOnUse" patternTransform="matrix(1 .45 -1 .65 480 -20)"><path d="M32 0H0V32" stroke="#91c9d5" strokeOpacity=".09" strokeWidth=".7"/></pattern>
        <clipPath id={id+'-road-clip'}><path d="M150 470 350 550 795 200 605 130Z"/></clipPath>
      </defs>

      <ellipse cx="490" cy="327" rx="420" ry="260" fill={'url(#'+id+'-halo)'}/>
      <g className="road-scene-orbit" stroke="#75e5f5" strokeWidth="1">
        <ellipse cx="478" cy="322" rx="397" ry="229" strokeOpacity=".12"/>
        <ellipse cx="478" cy="322" rx="421" ry="247" strokeOpacity=".1" strokeDasharray="2 13"/>
        <path d="M133 182A397 229 0 0 1 467 93M786 469A397 229 0 0 1 526 548" strokeOpacity=".5"/>
      </g>
      <path d="M55 349 381 88 873 290 547 565Z" fill="#03090d" stroke="#31434d" strokeOpacity=".4"/>
      <path d="M55 329 381 68 873 270 547 545Z" fill={'url(#'+id+'-ground)'} stroke={'url(#'+id+'-edge)'}/>
      <path d="M55 329 381 68 873 270 547 545Z" fill={'url(#'+id+'-grid)'}/>
      <g className="road-scene-topography" stroke="#75e5f5" strokeOpacity=".2" strokeWidth="1">
        <path d="M80 321C141 325 147 266 211 273S260 207 311 211 345 140 418 150 448 112 487 119"/>
        <path d="M90 342C157 354 173 302 229 302S285 234 329 246 369 168 438 180 478 140 520 145"/>
        <path d="M112 357C182 372 183 334 248 332S310 264 360 276 402 201 459 212 496 173 553 178"/>
        <path d="M132 374C202 397 215 359 271 364S335 296 388 306 426 238 484 244 529 210 581 212"/>
        <path d="M499 479C563 470 562 422 625 439S663 378 717 384 757 324 817 325"/>
        <path d="M520 496C584 495 591 451 646 466S681 411 739 418 783 355 833 351"/>
        <path d="M547 519C601 517 615 476 671 485S711 448 767 445 809 392 847 380"/>
      </g>
      <path d="M150 470 350 550 795 200 605 130Z" fill={'url(#'+id+'-road)'}/>
      <path d="M155 478 350 558 795 209V200L350 550 150 470Z" fill="#040b10"/>
      <path d="m164 466 187 73 430-338M165 458 440-324" stroke="#75e5f5" strokeOpacity=".25"/>
      <path d="m156 465 450-331M349 544 440-343" stroke={'url(#'+id+'-edge)'} strokeWidth="2"/>
      <g clipPath={'url(#'+id+'-road-clip)'}>
        <path className="road-scene-lanes" d="M243 512 700 165" stroke="#e2edf0" strokeOpacity=".6" strokeWidth="3" strokeDasharray="22 24"/>
        <path className="road-scene-traffic" d="m192 486 455-347" stroke="#75e5f5" strokeWidth="4" strokeLinecap="round" strokeDasharray="2 153"/>
        <path className="road-scene-traffic road-scene-traffic-return" d="m311 531 453-349" stroke="#f3bc74" strokeWidth="3" strokeLinecap="round" strokeDasharray="2 185"/>
        <g className="road-scene-beam"><path d="m141 480 218 87 74-58-218-87Z" fill={'url(#'+id+'-beam)'}/><path d="m215 422 218 87" stroke="#d8f561" strokeWidth="2"/></g>
        <path d="m424 342 13 8-3 12 16 8-1 11 17 7" stroke="#02090d" strokeWidth="7" strokeLinecap="round"/>
        <path d="m424 342 13 8-3 12 16 8-1 11 17 7" stroke="#8c9da0" strokeOpacity=".45" strokeWidth="1"/>
        <g className="road-scene-detection">
          <path d="M374 367 464 404 526 356 436 319Z" fill="#d8f561" fillOpacity=".055"/>
          <path className="road-scene-detection-line" d="M374 367 464 404 526 356 436 319Z" stroke="#d8f561" strokeWidth="1.5" strokeDasharray="350"/>
          <path d="M390 374 374 367 388 356M448 397 464 404 477 394M510 349 526 356 513 366M452 326 436 319 423 329" stroke="#e4ff92" strokeWidth="3"/>
        </g>
      </g>

      <g className="road-scene-callout road-scene-callout-main">
        <path d="m505 347 72-78h78" stroke="#d8f561" strokeOpacity=".65"/>
        <circle cx="505" cy="347" r="4" fill="#d8f561"/>
        <rect x="630" y="218" width="213" height="64" rx="10" fill="#0c1922" fillOpacity=".96" stroke="#d8f561" strokeOpacity=".45"/>
        <path d="M646 233h16m-16 5h10" stroke="#d8f561" strokeWidth="2"/>
        <text x="738" y="243" textAnchor="middle" className="road-scene-card-title" direction={lang==='ar'?'rtl':'ltr'}>{tx('SURFACE PATTERN','نمط سطح الطريق')}</text>
        <text x="738" y="265" textAnchor="middle" className="road-scene-card-note" direction={lang==='ar'?'rtl':'ltr'}>{tx('A closer look starts here','من هنا تبدأ المراجعة الدقيقة')}</text>
      </g>
      <g className="road-scene-callout road-scene-callout-secondary">
        <path d="M317 234h-92l-29-30" stroke="#75e5f5" strokeOpacity=".45"/>
        <circle cx="317" cy="234" r="3" fill="#75e5f5"/>
        <rect x="67" y="145" width="223" height="62" rx="10" fill="#0c1922" fillOpacity=".95" stroke="#75e5f5" strokeOpacity=".3"/>
        <circle cx="86" cy="163" r="3" fill="#75e5f5"/>
        <text x="178" y="169" textAnchor="middle" className="road-scene-card-title" direction={lang==='ar'?'rtl':'ltr'}>{tx('ROAD INTELLIGENCE','فهم أذكى للطريق')}</text>
        <text x="178" y="190" textAnchor="middle" className="road-scene-card-note" direction={lang==='ar'?'rtl':'ltr'}>{tx('Observe · inspect · improve','شاهد · افحص · حسّن')}</text>
      </g>
      <g className="road-scene-radar" transform="translate(758 424)">
        <circle r="41" fill="#0b1821" stroke="#75e5f5" strokeOpacity=".25"/>
        <circle r="28" stroke="#75e5f5" strokeOpacity=".13"/>
        <circle r="14" stroke="#75e5f5" strokeOpacity=".13"/>
        <path d="M-34 0h68M0-34v68" stroke="#75e5f5" strokeOpacity=".14"/>
        <g className="road-scene-radar-sweep"><path d="M0 0 0-34A34 34 0 0 1 29 17Z" fill="#75e5f5" fillOpacity=".12"/><path d="M0 0V-34" stroke="#75e5f5" strokeOpacity=".8"/></g>
        <circle r="3" fill="#d8f561"/>
      </g>
      <g stroke="#75e5f5" strokeOpacity=".5"><path d="M67 112V95h25M838 500v17h-25"/><path d="M397 63v-9m-4 4h8M543 567v9m-4-4h8"/></g>
    </svg>
    <figcaption id={id+'-caption'} className="road-scene-caption"><span><span className="road-scene-caption-dot" aria-hidden="true"/>{tx('Illustrative scan · not a prediction','مسح توضيحي · ليس نتيجة تنبؤ')}</span><button type="button" className="road-scene-motion" aria-pressed={playing} onClick={onToggle}>{playing?<Pause size={13} aria-hidden="true"/>:<Play size={13} aria-hidden="true"/>}{playing?tx('Pause animations','إيقاف الحركة'):tx('Play animations','تشغيل الحركة')}</button></figcaption>
  </figure>;
}
