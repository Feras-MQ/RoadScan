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
    'analyze my report data', 'my password', 'x'.repeat(301), 'photography']) {
    assert.equal(matchGuideTopic(query), null, query);
  }
});

test('navigation accepts only curated topic IDs and never a URL or command', () => {
  const expected = {
    upload: ['dashboard', 'guide-inspection'], compare: ['reports', 'guide-model-vote'],
    review: ['reports', 'review-annotations'], video: ['live', 'guide-live'],
    save: ['reports', 'review-decision'], export: ['reports', 'review-queue'],
    map: ['map', 'guide-map'], settings: ['settings', 'guide-settings'], errors: ['settings', 'guide-settings'],
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
