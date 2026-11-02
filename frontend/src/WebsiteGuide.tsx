import {useEffect, useRef, useState} from 'react';
import {ArrowUpRight, BookOpen, X} from 'lucide-react';
import {guideDestination, guideTopics, matchGuideTopic, screenNames} from './guideContent';
import type {GuideScreen, GuideTopic} from './guideContent';
import './websiteGuide.css';

type Props = {
  lang: string;
  screen: GuideScreen;
  hasReport: boolean;
  requestedTopic?: {id: string; version: number};
  onNavigate: (screen: GuideScreen) => string | null;
};

export default function WebsiteGuide({lang, screen, hasReport, requestedTopic, onNavigate}: Props) {
  const copy = (value: readonly [string, string]) => value[lang === 'ar' ? 1 : 0];
  const tx = (en: string, ar: string) => copy([en, ar]);
  const dialog = useRef<HTMLDialogElement>(null);
  const launcher = useRef<HTMLButtonElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const answerHeading = useRef<HTMLHeadingElement>(null);
  const [open, setOpen] = useState(false);
  const [topic, setTopic] = useState<GuideTopic | null>(null);
  const [question, setQuestion] = useState('');
  const [unmatched, setUnmatched] = useState(false);
  const [notice, setNotice] = useState('');
  const [highlight, setHighlight] = useState<{screen: GuideScreen; target: string} | null>(null);

  function close() {
    dialog.current?.close();
    setOpen(false);
    setQuestion('');
    setNotice('');
    (returnFocus.current?.isConnected ? returnFocus.current : launcher.current)?.focus({preventScroll: true});
  }
  function show() {
    returnFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : launcher.current;
    setHighlight(null);
    setTopic(null);
    setUnmatched(false);
    setNotice('');
    setOpen(true);
    dialog.current?.showModal();
    heading.current?.focus();
  }
  function selectTopic(next: GuideTopic | null) {
    setTopic(next);
    setUnmatched(!next);
    setNotice('');
  }
  function navigate() {
    const destination = topic && guideDestination(topic.id, hasReport);
    if (!destination) return;
    const blocked = onNavigate(destination.screen);
    if (blocked) {setNotice(blocked); return;}
    close();
    setHighlight(destination);
  }

  useEffect(() => {
    if (!highlight) return;
    if (highlight.screen !== screen) {setHighlight(null); return;}
    const element = document.getElementById(highlight.target);
    if (!element) {setHighlight(null); return;}
    element.classList.add('website-guide-highlight');
    // Run after the workspace's own screen/focus effects.
    const frame = window.requestAnimationFrame(() => {
      element.scrollIntoView({block: 'center', behavior: 'instant'});
      element.focus({preventScroll: true});
    });
    const timeout = window.setTimeout(() => setHighlight(null), 8000);
    return () => {window.cancelAnimationFrame(frame); window.clearTimeout(timeout); element.classList.remove('website-guide-highlight');};
  }, [highlight, screen]);
  useEffect(() => {if (open && topic) answerHeading.current?.focus();}, [topic, open]);
  useEffect(() => {
    if (requestedTopic) {show(); selectTopic(guideTopics.find(item => item.id === requestedTopic.id) || null);}
  }, [requestedTopic]);

  // The native modal handles focus containment and makes the underlying workspace inert.
  return <>
    <button ref={launcher} className="website-guide-launcher" aria-haspopup="dialog" aria-expanded={open} aria-controls="website-guide" onClick={show}>
      <BookOpen size={19}/><span>{tx('Website guide', 'دليل الموقع')}<small aria-hidden="true">{tx('Steps & navigation', 'خطوات وانتقال للشاشات')}</small></span>
    </button>
    {highlight && <div className="website-guide-hint" role="status">
      <span>{tx('Highlighted where to continue. Open the guide again for steps.', 'تم تحديد مكان المتابعة. افتح الدليل مجددًا لعرض الخطوات.')}</span>
      <button aria-label={tx('Dismiss highlight', 'إخفاء التحديد')} onClick={() => setHighlight(null)}><X size={18}/></button>
    </div>}
    <dialog ref={dialog} id="website-guide" className="website-guide" dir={lang === 'ar' ? 'rtl' : 'ltr'} aria-labelledby="website-guide-title" aria-describedby="website-guide-description"
      onKeyDown={event => {
        if (event.key !== 'Tab') return;
        const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled)')).filter(element => element.getClientRects().length);
        const first = controls[0], last = controls[controls.length - 1];
        if (event.shiftKey && (document.activeElement === first || !controls.includes(document.activeElement as HTMLElement))) {event.preventDefault(); last?.focus();}
        else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first?.focus();}
      }}
      onCancel={event => {event.preventDefault(); close();}} onClick={event => {if (event.target === event.currentTarget) close();}}>
      <div className="website-guide-body">
        <header className="website-guide-header"><h2 id="website-guide-title" ref={heading} tabIndex={-1}>{tx('Website guide', 'دليل الموقع')}</h2><button className="icon-button" aria-label={tx('Close guide', 'إغلاق الدليل')} onClick={close}><X size={20}/></button></header>
        <p id="website-guide-description">{tx('Short, curated instructions — not an AI chat. Questions stay in this panel; no reports or files are read by the guide.', 'تعليمات مختصرة ومعدّة مسبقًا، وليست محادثة ذكاء اصطناعي. تبقى الأسئلة داخل هذه اللوحة؛ لا يقرأ الدليل البلاغات أو الملفات.')}</p>
        <p className="website-guide-context">{tx('Current screen: ', 'الشاشة الحالية: ')}<strong>{copy(screenNames[screen])}</strong></p>
        <h3>{tx('For this screen', 'لهذه الشاشة')}</h3>
        <div className="website-guide-topics">{guideTopics.filter(item => item.screen === screen).map(item => <button key={item.id} onClick={() => selectTopic(item)}>{copy(item.title)}</button>)}</div>
        <form onSubmit={event => {event.preventDefault(); selectTopic(matchGuideTopic(question));}}>
          <label htmlFor="website-guide-question">{tx('What would you like to do?', 'ماذا تريد أن تفعل؟')}</label>
          <div className="website-guide-search"><input id="website-guide-question" value={question} onChange={event => setQuestion(event.target.value)} maxLength={300} autoComplete="off" placeholder={tx('For example: compare models', 'مثلًا: مقارنة النماذج')}/><button className="secondary" disabled={!question.trim()}>{tx('Find steps', 'عرض الخطوات')}</button></div>
          <small>{tx('Use a short website question. Do not enter tokens or personal information.', 'اكتب سؤالًا قصيرًا عن الموقع. لا تدخل رموز الوصول أو معلومات شخصية.')}</small>
        </form>
        <div aria-live="polite" aria-atomic="true">
          {unmatched && <p className="website-guide-notice">{tx('I do not have a clear guide for that question. Choose a topic below or try a short phrase such as “upload photo”. I cannot analyze reports or carry out commands.', 'لا توجد لدي تعليمات واضحة لهذا السؤال. اختر موضوعًا أدناه أو جرّب عبارة قصيرة مثل «رفع صورة». لا أستطيع تحليل البلاغات أو تنفيذ الأوامر.')}</p>}
          {topic && <section className="website-guide-answer" aria-labelledby="website-guide-topic">
            <h3 id="website-guide-topic" ref={answerHeading} tabIndex={-1}>{copy(topic.title)}</h3>
            <ol>{topic.steps.map((step, index) => <li key={index}>{copy(step)}</li>)}</ol>
            {topic.needsReport && !hasReport && <p>{tx('First select a report in Review queue. Then reopen this guide, choose this topic again, and select Open this screen to highlight the control inside the report.', 'اختر بلاغًا أولًا في قائمة المراجعة. ثم افتح الدليل مجددًا، واختر هذا الموضوع مرة أخرى، واضغط «افتح هذه الشاشة» لتحديد الأداة داخل البلاغ.')}</p>}
            <button className="primary" onClick={navigate}>{tx('Open this screen', 'افتح هذه الشاشة')}<ArrowUpRight size={17}/></button>
            <p className="website-guide-destination">{copy(screenNames[topic.screen])} · {tx('Navigation only; you choose the next action.', 'انتقال فقط؛ أنت تختار الإجراء التالي.')}</p>
            <button className="text-button" onClick={() => {setTopic(null); setNotice(''); setQuestion(''); heading.current?.focus();}}>{tx('Back to topics', 'العودة إلى المواضيع')}</button>
          </section>}
        </div>
        {notice && <p className="website-guide-notice" role="alert">{notice}</p>}
        <h3>{tx('All topics', 'كل المواضيع')}</h3>
        <div className="website-guide-topics">{guideTopics.map(item => <button key={item.id} aria-pressed={topic?.id === item.id} onClick={() => selectTopic(item)}>{copy(item.title)}</button>)}</div>
      </div>
    </dialog>
  </>;
}
