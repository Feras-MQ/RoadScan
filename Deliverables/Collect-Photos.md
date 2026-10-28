# Collect the missing road evidence

**Deadline: Saturday, 31 October 2026. No real local test photos have been supplied yet.**

1. **Aim for 80 photos:** 40 Saudi road spots, two different views of each spot. Include all four damage classes where available, plus some undamaged roads and distinct nearby defects.
2. **Separate groups before testing:** reserve 10 spots (20 photos) for duplicate calibration and 30 different spots (60 photos) for the final local test. Keep nearby spots from the same road segment in one group/split; do not split adjacent video frames between groups.
3. **Name pairs clearly:** `site01_a.jpg`, `site01_b.jpg`. Record the road/capture group, whether both views show the same physical defect, and real coordinates if known. Do not invent coordinates or labels.
4. **Check every box:** use RoadScan Review to correct all damage boxes and classes; save as Confirmed. In Approve this example, use the capture group and **val** or **test**, never train, for these protected examples; export from Learning.
5. **Keep test data untouched:** choose duplicate thresholds using validation groups only, then evaluate once on held-out groups. Do not change detector thresholds after seeing local test results.

**For the app's GPS duplicate demonstration:** upload each paired photo individually with its coordinates; batch uploads deliberately omit location. Pair matching also needs genuine different-defect comparisons, not only two views of the same defect.

Capture from a safe stationary position or as a passenger; avoid identifiable people and plates. Keep original collection files separately from the app's metadata-stripped copies. Once collected, the scripts can produce real local metrics; the plan above is not collected evidence.
