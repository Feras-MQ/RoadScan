# Third-party notices and design references

RoadScan's hero border motion adapts the public **Glowing border animation** Pen by Josh Sanger (`joshsanger-the-looper`):
https://codepen.io/joshsanger-the-looper/pen/LYvGZEY

The adaptation changes the colors, dimensions, animation speed and integration. It uses the Pen's masked border and CSS motion-path approach. The remaining dashboard layout, road illustration and interface implementation were written for RoadScan. The CSS Grid dashboard by `moaazalabed` was inspected for design inspiration, without copying its scripts, assets or chart dependencies:
https://codepen.io/moaazalabed/pen/jOJOLLP

CodePen's public-Pen licensing policy: https://blog.codepen.io/documentation/licensing/

## MIT License — adapted border effect

Copyright (c) Josh Sanger (https://codepen.io/joshsanger-the-looper)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Optional detector training data and framework

The separate model-training package uses RDD2022, by Deeksha Arya, Hiroya Maeda, Sanjay Kumar Ghosh, Durga Toshniwal and Yoshihide Sekimoto, DOI https://doi.org/10.6084/m9.figshare.21431547.v1. The original Figshare API metadata identifies CC BY 4.0: https://creativecommons.org/licenses/by/4.0/. Preparation selects country-disjoint subsets and converts Pascal VOC annotations into four-class YOLO labels; provenance records the transformations and file hashes. Dataset images/labels are not included in the verified-source archive.

The tested detector-enabled runtime (2026-10-26.2) includes Ultralytics 8.4.175. Ultralytics publishes its framework and YOLO trained-model licensing under AGPL-3.0 by default, with separate Enterprise terms: https://www.ultralytics.com/license. The upstream license is https://github.com/ultralytics/ultralytics/blob/main/LICENSE. The CodePen effect's MIT license does not cover Ultralytics, model weights or training data. Third-party terms and the license for RoadScan's own contributions must be documented separately; this notice grants no additional rights. See Deliverables/Models.md for current model-release conditions.
