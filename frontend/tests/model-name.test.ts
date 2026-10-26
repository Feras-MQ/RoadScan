import assert from 'node:assert/strict';
import {test} from 'node:test';
import {modelName} from '../src/modelName.ts';

test('model display names keep architecture, dataset, resolution and checkpoint distinct', () => {
  assert.equal(modelName('RTDETR_L_RDD2022_200E_800px_best_Epoch068_mAP50_95_0.31278'), 'RT-DETR L · RDD2022 · 800 px · Epoch 68');
  assert.equal(modelName('YOLOv8m_RDD2022_150E_800px_best_Epoch021_mAP50_95_0.30855'), 'YOLOv8m · RDD2022 · 800 px · Epoch 21');
  assert.equal(modelName('RoadScan original YOLO11n baseline',640), 'YOLO11n · Baseline · 640 px');
  assert.notEqual(modelName('road_damage_rtdetr_x_best_Epoch001'),modelName('road_damage_rtdetr_x_final_best_Epoch050'));
  assert.equal(modelName('custom_model'), 'custom model');
  assert.equal(modelName('main_yolo26s_1024.pt'), 'YOLO26s · Main · 1024 px');
  assert.equal(modelName('e3_yolo26s_640_no_augmentation.pt'), 'YOLO26s · No augmentation · 640 px');
  assert.notEqual(modelName('e2_yolo26s_640.pt'), modelName('e3_yolo26s_640_vertical_flip.pt'));
});
