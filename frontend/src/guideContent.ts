export type GuideScreen = 'dashboard' | 'reports' | 'settings' | 'live' | 'learning' | 'map';
type Copy = readonly [string, string];
export type GuideTopic = {
  id: string;
  title: Copy;
  screen: GuideScreen;
  target: string;
  needsReport?: boolean;
  phrases: string[];
  steps: Copy[];
};

export const screenNames: Record<GuideScreen, Copy> = {
  dashboard: ['Overview', 'نظرة عامة'], reports: ['Review queue', 'قائمة المراجعة'],
  live: ['Live recognition', 'التعرف المباشر'], map: ['Map & results', 'الخريطة والنتائج'],
  settings: ['Settings', 'الإعدادات'], learning: ['Learning', 'التعلّم'],
};

// Curated instructions only. This module has no access to reports, files or network APIs.
export const guideTopics: GuideTopic[] = [
  {id: 'upload', title: ['Upload and analyze a photo', 'رفع صورة وتحليلها'], screen: 'dashboard', target: 'guide-inspection',
    phrases: ['upload', 'photo', 'image', 'new inspection', 'analyze image', 'رفع', 'صورة', 'صور', 'تحليل صورة', 'فحص جديد'], steps: [
      ['In Overview, find New inspection and choose Browse files. Use JPEG, PNG or WebP within the displayed size limit (up to 25 megapixels).', 'في نظرة عامة، انتقل إلى فحص جديد واختر اختيار صور. استخدم JPEG أو PNG أو WebP ضمن حد الحجم المعروض (حتى 25 ميجابكسل).'],
      ['For one photo, you can add latitude and longitude in Add location (optional). Crop or blur faces and plates before submitting.', 'للصورة الواحدة، يمكنك إدخال خط العرض وخط الطول في إضافة موقع (اختياري). قص أو موّه الوجوه واللوحات قبل الإرسال.'],
      ['Connect your workspace, then choose Analyze & create report. Without a detector, the button is Create report for review. Check the result in Review queue.', 'اتصل بمساحة العمل ثم اختر تحليل وإنشاء بلاغ. عند غياب النموذج يظهر زر إنشاء بلاغ للمراجعة. راجع النتيجة في قائمة المراجعة.'],
    ]},
  {id: 'compare', title: ['Compare models', 'مقارنة النماذج'], screen: 'reports', target: 'guide-model-vote', needsReport: true,
    phrases: ['compare models', 'model comparison', 'model voting', 'model vote', 'compare', 'مقارنة النماذج', 'تصويت النماذج', 'قارن', 'مقارنة'], steps: [
      ['In Review queue, open a saved report and save any review changes first.', 'في قائمة المراجعة، افتح بلاغًا محفوظًا واحفظ تغييرات المراجعة أولًا.'],
      ['Find Model voting below the review decision. Open Choose voting models, select two or three available models, then choose Run model vote.', 'انتقل إلى تصويت النماذج أسفل قرار المراجعة. افتح اختيار نماذج التصويت وحدد نموذجين أو ثلاثة من المتاح، ثم اختر تشغيل تصويت النماذج.'],
      ['Inspect agreement and individual results. Replacing draft boxes is your choice; check them and Save review separately. Agreement and voting scores are not accuracy.', 'افحص الاتفاق ونتائج كل نموذج. استبدال تحديدات المسودة قرارك؛ راجعها ثم اختر حفظ المراجعة بشكل منفصل. الاتفاق ودرجات التصويت ليست قياسًا للدقة.'],
    ]},
  {id: 'review', title: ['Review and edit detections', 'مراجعة التحديدات وتعديلها'], screen: 'reports', target: 'review-annotations', needsReport: true,
    phrases: ['review', 'detections', 'annotations', 'boxes', 'edit', 'مراجعة', 'تحديدات', 'مربعات', 'تعديل'], steps: [
      ['Open a report in Review queue. Inspect the image and use Compare original to check the unannotated photo.', 'افتح بلاغًا في قائمة المراجعة. افحص الصورة واستخدم مقارنة بالأصل لعرض الصورة دون التحديدات.'],
      ['In Damage annotations, choose the damage class and Draw boxes or Add box. You can edit coordinates or remove an incorrect box.', 'في تحديدات الضرر، اختر نوع الضرر ثم رسم المربعات أو إضافة مربع. يمكنك تعديل الإحداثيات أو حذف تحديد غير صحيح.'],
      ['Keep boxes inside the image. In Review decision, choose a status, add an Inspector note and Save review. Unsaved changes need your attention before opening another report.', 'أبقِ المربعات داخل الصورة. في قرار المراجعة، اختر الحالة وأضف ملاحظة المراجع ثم حفظ المراجعة. انتبه للتغييرات غير المحفوظة قبل فتح بلاغ آخر.'],
    ]},
  {id: 'video', title: ['Analyze a video', 'تحليل فيديو'], screen: 'live', target: 'guide-live',
    phrases: ['video', 'every frame', 'mov', 'mp4', 'upload video', 'upload mov', 'upload mp4', 'فيديو', 'رفع فيديو', 'كل اطار'], steps: [
      ['In Live recognition, set Source to Video · analyze every frame. If already in thorough analysis, its video controls are on screen.', 'في التعرف المباشر، اختر من المصدر فيديو · تحليل كل إطار. إذا كنت في التحليل الشامل بالفعل فستجد أدوات الفيديو أمامك.'],
      ['Choose a recording within the displayed 2 GiB limit. Select Quality and Frames to analyze; sampling fewer frames can reduce processing time.', 'اختر تسجيلًا ضمن الحد المعروض وهو 2 GiB. حدد الجودة والإطارات المحللة؛ تقليل عدد الإطارات قد يقلل وقت المعالجة.'],
      ['With a connected workspace and ready detector, press the analysis button yourself. Keep the tab visible; Stop analysis ends the run. No report is saved automatically.', 'بعد الاتصال بمساحة العمل وتجهيز النموذج، اضغط زر التحليل بنفسك. أبقِ التبويب ظاهرًا؛ إيقاف التحليل ينهي التشغيل. لا يُحفظ بلاغ تلقائيًا.'],
      ['Use selected frame for report returns a frame to Overview. Creating that report runs a new analysis for human review. Real-time preview samples frames; it does not analyze every frame.', 'استخدام الإطار المختار للتقرير يعيد الإطار إلى نظرة عامة. إنشاء البلاغ يجري تحليلًا جديدًا للمراجعة البشرية. المعاينة المباشرة تأخذ عينات ولا تحلل كل إطار.'],
    ]},
  {id: 'save', title: ['Save a review', 'حفظ المراجعة'], screen: 'reports', target: 'review-decision', needsReport: true,
    phrases: ['save', 'save review', 'status', 'حفظ', 'حفظ مراجعة', 'احفظ', 'حالة'], steps: [
      ['Uploading a photo creates a report. Later edits to its boxes, status and note remain a draft until you choose Save review.', 'رفع الصورة ينشئ بلاغًا. تعديل التحديدات أو الحالة أو الملاحظة يبقى مسودة حتى تختار حفظ المراجعة.'],
      ['Open the report in Review queue and find Review decision. Check the status and Inspector note, then choose Save review and wait for Review saved.', 'افتح البلاغ في قائمة المراجعة وانتقل إلى قرار المراجعة. تحقق من الحالة وملاحظة المراجع ثم اختر حفظ المراجعة وانتظر تم حفظ المراجعة.'],
      ['Confirm before assigning or resolving. Reopen a resolved report with Needs Review. If saving fails, keep the draft open and read the error before retrying.', 'أكد البلاغ قبل الإسناد أو الإغلاق. أعد فتح البلاغ المغلق باختيار بانتظار المراجعة. إذا فشل الحفظ، أبقِ المسودة مفتوحة واقرأ الخطأ قبل المحاولة مجددًا.'],
    ]},
  {id: 'export', title: ['Export reports', 'تصدير البلاغات'], screen: 'reports', target: 'review-queue',
    phrases: ['export', 'download', 'pdf', 'csv', 'تصدير', 'تنزيل', 'تحميل البلاغات'], steps: [
      ['This version has no report export button in the website. The guide cannot download reports or create a PDF or CSV.', 'لا يوجد زر لتصدير البلاغات في موقع هذه النسخة. لا يستطيع الدليل تنزيل البلاغات أو إنشاء PDF أو CSV.'],
      ['Use Review queue to view saved reports and Save review to store edits. Learning has a separate ZIP download of approved training examples; choose Download training examples in this guide for those steps.', 'استخدم قائمة المراجعة لعرض البلاغات وحفظ المراجعة لتخزين التعديلات. توفر شاشة التعلّم تنزيل ZIP لأمثلة التدريب المعتمدة بشكل منفصل؛ اختر تنزيل أمثلة التدريب في هذا الدليل لعرض الخطوات.'],
    ]},
  {id: 'training', title: ['Download training examples', 'تنزيل أمثلة التدريب'], screen: 'learning', target: 'guide-learning',
    phrases: ['training examples', 'approved dataset', 'download training examples', 'download approved training examples', 'download approved dataset', 'export training examples', 'export approved dataset', 'أمثلة التدريب', 'البيانات المعتمدة', 'تنزيل أمثلة التدريب', 'تحميل أمثلة التدريب', 'تنزيل البيانات المعتمدة', 'تصدير أمثلة التدريب', 'تصدير البيانات المعتمدة'], steps: [
      ['In Review queue, correct a report and save it as Confirmed. In Teach the next model, check the capture group, dataset split and required confirmations, then choose Approve this example yourself.', 'في قائمة المراجعة، صحح البلاغ واحفظه بحالة مؤكد. في علّم النموذج القادم، تحقق من مجموعة التصوير وتقسيم البيانات والتأكيدات المطلوبة، ثم اختر اعتماد هذا المثال بنفسك.'],
      ['Open Learning and check the approved counts. With export permission and at least one approved example, choose Export approved dataset. Otherwise ask an administrator; stale approvals are excluded.', 'افتح التعلّم وتحقق من أعداد الأمثلة المعتمدة. عند توفر صلاحية التصدير ومثال معتمد واحد على الأقل، اختر تصدير البيانات المعتمدة. وإلا فاطلب من المسؤول ذلك؛ تُستبعد الاعتمادات التي تحتاج مراجعة مجددًا.'],
      ['The ZIP contains approved images, YOLO boxes and split records. It is a training dataset, not a PDF or CSV report export. Downloading does not train or change your active model.', 'يحتوي ZIP على الصور المعتمدة وتحديدات YOLO وسجلات التقسيم. إنه بيانات تدريب وليس تصدير بلاغات PDF أو CSV. لا يؤدي التنزيل إلى تدريب النموذج أو تغيير النموذج المفعّل.'],
    ]},
  {id: 'map', title: ['Find reports on the map', 'عرض البلاغات على الخريطة'], screen: 'map', target: 'guide-map',
    phrases: ['map', 'location', 'coordinates', 'gps', 'خريطة', 'الخريطة', 'موقع', 'احداثيات'], steps: [
      ['Open Map & results. Recorded locations shows saved coordinates; Simulation shows simulated positions. This is a local coordinate view, without street tiles.', 'افتح الخريطة والنتائج. المواقع المسجلة تعرض الإحداثيات المحفوظة والمحاكاة تعرض مواقع افتراضية. هذا عرض إحداثيات محلي دون خرائط شوارع.'],
      ['Select a pin or report in the list to inspect it, then Open image & review. Reports without coordinates remain in the list.', 'اختر علامة أو بلاغًا من القائمة لفحصه ثم فتح الصورة والمراجعة. تبقى البلاغات التي لا تحمل إحداثيات في القائمة.'],
      ['The current report page and review filters apply here too. Change pages or clear filters in Review queue if a report is missing. Add a location when uploading a new photo.', 'تطبق هنا صفحة البلاغات وعوامل تصفية المراجعة الحالية. غيّر الصفحة أو امسح عوامل التصفية في قائمة المراجعة إذا لم تجد بلاغًا. أضف موقعًا عند رفع صورة جديدة.'],
    ]},
  {id: 'settings', title: ['Connection and model settings', 'الاتصال وإعدادات النموذج'], screen: 'settings', target: 'guide-settings',
    phrases: ['settings', 'connect', 'connection', 'token', 'model library', 'change model', 'تغيير النموذج', 'language', 'animations', 'اعدادات', 'لغة', 'اللغة', 'عربي', 'انجليزي', 'الحركة', 'اتصال', 'اتصل', 'رمز', 'مكتبة النماذج'], steps: [
      ['When disconnected, use Connect your workspace and enter your existing access token in its password field. Do not paste a token into this guide.', 'عند عدم الاتصال، استخدم اتصل بمساحة العمل وأدخل رمز الوصول الموجود لديك في حقل كلمة المرور. لا تلصق الرمز في هذا الدليل.'],
      ['Settings shows Road damage detector and Your model library. Importing or switching models requires an administrator token. The guide only points to the screen.', 'تعرض الإعدادات نموذج كشف ضرر الطريق ومكتبة النماذج. يتطلب استيراد النماذج أو تبديلها رمز مسؤول. الدليل يفتح الشاشة فقط.'],
      ['No detector? Photo upload and manual report review remain available. Use the language button in the top bar for Arabic or English, and Motion on/off for animations.', 'لا يوجد نموذج؟ يظل رفع الصور ومراجعة البلاغات يدويًا متاحين. استخدم زر اللغة أعلى الصفحة للعربية أو الإنجليزية وزر الحركة لتفعيلها أو إيقافها.'],
    ]},
  {id: 'errors', title: ['Troubleshoot common errors', 'حل المشكلات الشائعة'], screen: 'settings', target: 'guide-settings',
    phrases: ['error', 'failed', 'not working', 'unavailable', 'permission', '401', '403', 'خطا', 'فشل', 'لا يعمل', 'غير متاح', 'صلاحية'], steps: [
      ['For 401/403 or connection errors, check your existing token and role in Settings. Retry connection after correcting access; the guide cannot grant permissions.', 'لأخطاء 401 أو 403 أو الاتصال، تحقق من رمزك ودورك في الإعدادات. أعد الاتصال بعد تصحيح الوصول؛ لا يمنح الدليل صلاحيات.'],
      ['For an image error, check the format and displayed upload limit. For an unavailable camera, check browser camera permission yourself or use Browse files.', 'لخطأ الصورة، تحقق من الصيغة وحد الرفع المعروض. إذا تعذرت الكاميرا، تحقق بنفسك من إذن المتصفح أو استخدم اختيار صور.'],
      ['For a busy detector, wait for the current job. For failed video analysis, read its message and check the model/video; an incomplete run is not a complete review. Keep unsaved work open.', 'إذا كان النموذج مشغولًا، انتظر المهمة الحالية. عند فشل تحليل الفيديو، اقرأ الرسالة وتحقق من النموذج والفيديو؛ التشغيل غير المكتمل ليس مراجعة كاملة. أبقِ العمل غير المحفوظ مفتوحًا.'],
    ]},
];

function normalize(value: string) {
  return value.toLowerCase().normalize('NFKC').replace(/[\u064b-\u065f\u0670\u0640]/g, '')
    .replace(/[أإآ]/g, 'ا').replace(/ى/g, 'ي').replace(/ة/g, 'ه').replace(/[^\p{L}\p{N}]+/gu, ' ')
    .replace(/(^| )و(?=[\u0621-\u064a]{2})/g, '$1و ').trim().split(/\s+/)
    .filter(word => !['a', 'an', 'the', 'my', 'your', 'our'].includes(word))
    .map(word => word.replace(/^ال(?=[\u0621-\u064a]{2})/, '')).join(' ');
}

export function matchGuideTopic(question: string): GuideTopic | null {
  if (question.length > 300) return null;
  const query = normalize(question);
  // shortcut: intentionally conservative phrase matching; expand only with tested website questions.
  if (/\b(delete|erase|password|diagnose|execute)\b|حذف|امسح كل|كلمه مرور/.test(query)) return null;
  const words = query.split(' ');
  const hits: {topic: GuideTopic; start: number; end: number}[] = [];
  for (const topic of guideTopics) for (const phrase of topic.phrases) {
    const tokens = normalize(phrase).split(' ');
    words.forEach((_, start) => {
      if (tokens.every((token, index) => token === words[start + index])) hits.push({topic, start, end: start + tokens.length});
    });
  }
  // A compound phrase consumes its generic words; separate conflicting topics still need clarification.
  const specific = hits.filter(hit => !hits.some(other => other.start <= hit.start && other.end >= hit.end && other.end - other.start > hit.end - hit.start));
  return new Set(specific.map(hit => hit.topic.id)).size === 1 ? specific[0].topic : null;
}

export function guideDestination(id: string, hasReport: boolean): {screen: GuideScreen; target: string} | null {
  const topic = guideTopics.find(topic => topic.id === id);
  return topic ? {screen: topic.screen, target: topic.needsReport && !hasReport ? 'review-queue' : topic.target} : null;
}
