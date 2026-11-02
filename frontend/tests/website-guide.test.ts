import assert from 'node:assert/strict';
import {test} from 'node:test';
import {guideDestination, guideTopics, matchGuideTopic} from '../src/guideContent.ts';

test('short English and Arabic questions find factual website instructions', () => {
  for (const [query, id] of [
    ['How do I upload a photo?', 'upload'], ['HOW DO I COMPARE MODELS?', 'compare'],
    ['How to edit detections?', 'review'], ['Analyze video', 'video'],
    ['save review', 'save'], ['Export PDF', 'export'], ['Where is the map?', 'map'],
    ['connection token', 'settings'], ['401 error', 'errors'],
    ['كيف أرفع صُورة؟', 'upload'], ['مُقارنة النَّماذج', 'compare'],
    ['تعديل التحديدات', 'review'], ['تحليل فيديو', 'video'], ['كيف احفظ', 'save'],
    ['تصدير البلاغات', 'export'], ['الخريطة', 'map'], ['إعدادات', 'settings'], ['خَطَأ', 'errors'],
  ]) assert.equal(matchGuideTopic(query)?.id, id, query);
});

test('unknown, ambiguous and unsupported commands get an honest fallback', () => {
  for (const query of ['', '   ', 'weather tomorrow', 'this pothole is dangerous?',
    'delete all reports', 'execute upload command', 'حذف البلاغات', 'photo video',
    'analyze my report data', 'my password', 'x'.repeat(301), 'photography',
    'upload a video and a photo', 'save my review and compare models',
    'download training examples or export PDF', 'رفع فيديو وصورة', 'train a model']) {
    assert.equal(matchGuideTopic(query), null, query);
  }
});

test('specific curated phrases handle filler words and Arabic normalization without guessing mixed intents', () => {
  for (const [query, id] of [
    ['upload video', 'video'], ['how do I upload a video', 'video'], ['upload a mov file', 'video'],
    ['UPLOAD THE MP4 FILE!', 'video'], ['رفع فيديو', 'video'], ['كيف يتم رَفْع الـفِيدْيُو؟', 'video'],
    ['how to save my review', 'save'], ['save the review', 'save'], ['حفظ المُراجعة', 'save'],
    ['change the model', 'settings'], ['change my model', 'settings'], ['تغيير النموذج', 'settings'],
    ['download training examples', 'training'], ['download the approved training examples', 'training'],
    ['export approved dataset', 'training'], ['download approved dataset', 'training'], ['export training examples', 'training'],
    ['تنزيل أمثلة التدريب', 'training'], ['تصدير البيانات المعتمدة', 'training'], ['تنزيل البيانات المعتمدة', 'training'],
    ['upload a photo', 'upload'], ['export to pdf', 'export'], ['download reports', 'export'],
  ]) assert.equal(matchGuideTopic(query)?.id, id, query);
});

test('exact plural photo phrases keep mixed and unsupported requests conservative', () => {
  for (const query of ['analyze images', 'how to analyze images', 'road photos', 'inspect road photos',
    'رفع صورتي', 'كيف أحلل الصور؟', 'تحليل الصور']) {
    assert.equal(matchGuideTopic(query)?.id, 'upload', query);
  }
  for (const query of ['analyze images and compare models', 'road photos and export PDF',
    'delete road photos', 'execute analyze images', 'حذف road photos',
    'analyze images and حذف البلاغات', 'images', 'photos', 'analyze videos']) {
    assert.equal(matchGuideTopic(query), null, query);
  }
});

test('navigation accepts only curated topic IDs and never a URL or command', () => {
  const expected = {
    upload: ['dashboard', 'guide-inspection'], compare: ['reports', 'guide-model-vote'],
    review: ['reports', 'review-annotations'], video: ['live', 'guide-live'],
    save: ['reports', 'review-decision'], export: ['reports', 'review-queue'],
    map: ['map', 'guide-map'], settings: ['settings', 'guide-settings'], errors: ['settings', 'guide-settings'],
    training: ['learning', 'guide-learning'],
    'map-location': ['dashboard', 'guide-inspection'],
  };
  for (const [id, [screen, target]] of Object.entries(expected)) {
    assert.deepEqual(guideDestination(id, true), {screen, target});
  }
  for (const id of ['compare', 'review', 'save']) assert.deepEqual(guideDestination(id, false), {screen: 'reports', target: 'review-queue'});
  for (const id of ['https://example.com', 'javascript:alert(1)', '/api/reports', 'delete', '__proto__', '']) assert.equal(guideDestination(id, true), null);
  assert.equal(new Set(guideTopics.map(topic => topic.id)).size, guideTopics.length);
  for (const topic of guideTopics) {
    assert.ok(topic.title.every(Boolean));
    assert.ok(topic.steps.length >= 2 && topic.steps.every(step => step.every(Boolean)));
  }
});

test('map questions explain missing pins and location entry without claiming GPS collection', () => {
  for (const query of ['why are there no pins?', 'missing GPS', 'my photo has no GPS', 'لا توجد نقاط', 'الموقع مفقود']) {
    assert.equal(matchGuideTopic(query)?.id, 'map', query);
  }
  for (const query of ['add a location', 'how do I add a location to a photo?', 'add GPS to my photo', 'add coordinates to a photo', 'add a location to a new photo', 'add coordinates', 'photo location', 'location source', 'إضافة الموقع', 'إضافة إحداثيات', 'إضافة موقع إلى الصورة', 'إضافة إحداثيات إلى الصورة', 'موقع الصورة', 'مصدر الموقع']) {
    assert.equal(matchGuideTopic(query)?.id, 'map-location', query);
  }
  for (const query of ['add location and analyze video', 'upload photo and delete location', 'إضافة موقع وحذف البلاغ']) {
    assert.equal(matchGuideTopic(query), null, query);
  }
  const map = guideTopics.find(topic => topic.id === 'map')!;
  assert.match(map.steps.map(step => step[0]).join(' '), /no streets, routes or distance scale/);
  const location = guideTopics.find(topic => topic.id === 'map-location')!;
  assert.match(location.steps.map(step => step[0]).join(' '), /GPS is not extracted automatically/);
});

test('map UI labels and video-report location questions match without swallowing mixed intents', () => {
  for (const query of ['recorded locations', 'simulated locations', 'simulation', 'no usable location',
    'What are the recorded locations?', 'مواقع مسجلة', 'مواقع محاكاة', 'محاكاة', 'بلا موقع صالح', 'المواقع المُسجَّلة']) {
    assert.equal(matchGuideTopic(query)?.id, 'map', query);
  }
  for (const query of ['where is my video report on the map', 'video report location', 'location of my video report',
    'where are my video reports on the map?', 'video GPS', 'موقع بلاغ الفيديو', 'أين بلاغ الفيديو على الخريطة؟',
    'وين بلاغ الفيديو في الخريطة', 'إحداثيات الفيديو']) {
    assert.equal(matchGuideTopic(query)?.id, 'map-location', query);
  }
  for (const query of ['analyze video', 'upload a video', 'how do I upload a mov file', 'تحليل الفيديو', 'رفع فيديو']) {
    assert.equal(matchGuideTopic(query)?.id, 'video', query);
  }
  for (const query of ['recorded locations and analyze video', 'simulation and save review',
    'video report location and upload photo', 'where is my video report on the map and analyze video',
    'مواقع مسجلة وتحليل فيديو', 'موقع بلاغ الفيديو وتحليل فيديو', 'حذف مواقع المحاكاة']) {
    assert.equal(matchGuideTopic(query), null, query);
  }
});
