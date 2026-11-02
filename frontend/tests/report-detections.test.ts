import assert from 'node:assert/strict';
import {test} from 'node:test';
import {inspectAnnotations, annotationSummary, reportPriority} from '../src/reportDetections.ts';
import {sameAnnotations, validAnnotations} from '../src/annotations.ts';

test('unreadable and non-displayable annotations never become an empty result or priority',()=>{
  const empty={detections:[],detections_readable:true,score:null};
  assert.deepEqual(inspectAnnotations(empty),{kind:'ready',boxes:[]});
  assert.equal(annotationSummary(empty,'en'),'0 annotations');
  for(const detections of [null,[{class_id:'D40'}],[{class_id:['D40'],box:[1,2,3,4]}],[null],[{class_id:'D40',box:[0,0,NaN,4]}]]) {
    const report={detections,detections_readable:detections!==null,score:90};
    assert.equal(inspectAnnotations(report).boxes,null);
    assert.equal(reportPriority(report),null);
    assert.doesNotMatch(annotationSummary(report,'en'),/0 annotations/);
    assert.match(annotationSummary(report,'ar'),/غير قابلة/);
  }
  assert.equal(inspectAnnotations({detections:[],detections_readable:false}).kind,'unreadable');
});

test('legacy missing weights display without fabrication and require a weight only for annotation edits',()=>{
  const stored={detections:[{class_id:'D40',box:[1,2,30,40]}],score:85};
  const result=inspectAnnotations(stored);
  assert.equal(result.kind,'legacy');assert.equal(result.boxes![0].confidence,undefined);
  assert.equal(validAnnotations(result.boxes!,100,100),false);
  assert.equal(reportPriority(stored),null);
  assert.match(annotationSummary(stored,'en'),/confidence not recorded/);
  assert.equal(sameAnnotations(result.boxes!,inspectAnnotations(stored).boxes!),true);
  assert.equal(sameAnnotations(result.boxes!,[{...result.boxes![0],confidence:0}]),false);
  result.boxes![0].box[0]=7;
  assert.equal(stored.detections[0].box[0],1,'draft geometry does not mutate the saved record');
});
