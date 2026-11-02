# Website guide

The **Website guide / دليل الموقع** button opens a bilingual help panel on every
screen, including before connection. It offers common topics, suggestions for the
current screen, and short typed questions matched to curated instructions. Matching
normalizes common English articles/possessives and Arabic articles/diacritics.
Specific phrases consume their generic words (for example, "upload video"), while
separate conflicting intents still fall back instead of guessing. It is
not an LLM, report explainer, or command executor. Questions are kept in component
memory and cleared when the panel closes. The guide receives only language,
screen, whether a report is selected, an optional curated topic request, and a
navigation callback. The map's **How this map works** button requests the map
topic directly; closing returns focus to that button. The floating launcher also
states **Steps & navigation**, and current-screen topics appear before the question
field.

Topics cover photo upload, model voting, detection editing, video analysis,
saving reviews, report export availability, training-data download, map use,
settings, and common errors. Map help explains the coordinate diagram, page scope,
independent filters, missing/unknown locations, simulation and explicit external links.
**Add a location to a new photo** opens Overview and explains manual entry without
claiming automatic GPS extraction or editing of saved coordinates.
There is no website PDF/CSV report-export control in
this baseline. Learning separately offers **Export approved dataset**, a ZIP of
approved training examples; its guide topic opens Learning without downloading.
Instructions and both languages live in `frontend/src/guideContent.ts`;
update them when the actual UI labels or workflows change.

**Open this screen** uses an allowlisted topic destination and the existing screen
state. It never starts a camera, uploads media, selects models, saves a review, or
changes a permission. When a report is needed but none is selected, it opens the
review queue and asks the user to select one. A temporary outline and keyboard
focus point to the relevant panel; it clears after eight seconds, navigation,
dismissal, or reopening the guide. The modal supports Escape, a sticky Close
button, focus containment/return, and Arabic RTL.

Shared screen navigation from the guide, sidebar, brand and other screen buttons
is silent unless leaving would lose or interrupt real work:

- Clicking the current screen does nothing and keeps its local state.
- A running App-level task or photo batch blocks the change until it finishes.
- Unsaved review edits block leaving Review queue until they are saved. Boxes,
  status or note count as edited only when they differ from the saved report;
  reordered or reverted boxes count as unchanged. An unsaved annotation
  replacement draft also counts as an edit.
- Open tools register their own unfinished work only while it exists: model-vote
  results or changed model choices, unsaved training settings, a processed live
  frame, unsaved video-analysis results, and a running vote, analysis, live
  session or dataset export. If any is present, one confirmation lists it;
  Cancel keeps it, Continue stops or discards it.
- A training-approval save or model-library update in progress blocks
  navigation until it finishes.
- An open camera preview is stopped without asking.

Opening another report with unsaved review edits shows the Keep editing /
Discard and open banner instead of a dialog; Discard and open skips the
tool confirmation. Explicit workflow handoffs (opening a report or using a
captured frame) retain their existing behavior. Browser-history routing is not
implemented.

The full-video heading and intro reflect the selected sampling rate in both
languages. The every-frame wording appears only for the Every frame option.

## Verification

Run from `frontend` with the project's dependencies already present. The verified
Windows setup used **Node.js 24.22.2**, **Playwright 1.64.1**, and an already
installed **Google Chrome**. Keep the Playwright test package in a separate QA
directory, outside the repository's dependencies; these commands install nothing
and do not download a browser.

```sh
node --version
node --test tests/*.test.ts
node node_modules/typescript/bin/tsc --noEmit -p tsconfig.json
```

`tests/website-guide.browser.mjs` is the executable entry point: run it directly;
no importing runner or backend server is needed. It serves `frontend/dist`, so
rebuild before every check of changed source. Set both Playwright variables to
**file URLs**, not filesystem paths. `ROADSCAN_CHROME` is an executable path;
`ROADSCAN_QA_OUTPUT` is a directory for generated screenshots.

PowerShell example, still from `frontend`. The QA directory and Chrome path below
are **example paths**: replace them with your existing installation locations.
The QA directory must already contain `node_modules/playwright` version 1.64.1.

```powershell
$qaRoot = Join-Path $env:TEMP 'roadscan-browser-qa'
$playwrightRoot = Join-Path $qaRoot 'node_modules\playwright'
$env:ROADSCAN_PLAYWRIGHT_MODULE = ([uri](Join-Path $playwrightRoot 'index.mjs')).AbsoluteUri
$env:ROADSCAN_PLAYWRIGHT_EXPECT = ([uri](Join-Path $playwrightRoot 'test.mjs')).AbsoluteUri
$env:ROADSCAN_CHROME = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$env:ROADSCAN_QA_OUTPUT = Join-Path $qaRoot 'artifacts\website-guide'
node node_modules/vite/bin/vite.js build
if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed; do not run stale dist.' }
node tests/website-guide.browser.mjs
if ($LASTEXITCODE -ne 0) { throw 'Website guide browser check failed.' }
```

For Linux, use the same entry point and prerequisites. The following paths are
also examples; replace them with existing installations. File URLs containing
spaces must encode them as `%20`. This is the equivalent invocation, not a claim
that Linux was part of the verified Windows run.

```sh
export ROADSCAN_PLAYWRIGHT_MODULE='file:///tmp/roadscan-browser-qa/node_modules/playwright/index.mjs'
export ROADSCAN_PLAYWRIGHT_EXPECT='file:///tmp/roadscan-browser-qa/node_modules/playwright/test.mjs'
export ROADSCAN_CHROME='/usr/bin/google-chrome'
export ROADSCAN_QA_OUTPUT='/tmp/roadscan-browser-qa/artifacts/website-guide'
node node_modules/vite/bin/vite.js build && node tests/website-guide.browser.mjs
```

The harness creates the output directory. If `ROADSCAN_CHROME` is omitted, it
uses Playwright's `chrome` channel, which still requires installed Chrome. No
real workspace token, reports, model files or running RoadScan backend are needed.

The test serves only the built frontend and in-memory synthetic API fixtures on
a temporary localhost port. It uses fresh browser contexts, blocks external
requests, rejects API writes at the fixture server, and closes the browser/server afterward. It checks
English/Arabic at desktop and mobile sizes, typing/fallback, destinations,
keyboard/close/reopen, highlight cleanup, unsaved review guards, retained photo
selection, and disconnected help. The report-work regression additionally uses
three synthetic models and an eligible training fixture to exercise the actual
ModelVote/TrainingApproval components. Explicit test clicks start mocked vote
requests intercepted in the browser; no inference occurs. It verifies Cancel
preserves an in-flight vote, completed unapplied results, model choices, and
capture-group/split/checkbox edits. Continue discards local state and aborts an
in-flight vote only after confirmation. No model activation or training submission
is performed, and no actual report storage is read. The report and video guard
scenarios cover guide, sidebar and brand paths at 1440px and 390px widths. Video
responses are synthetic: Cancel retains the pending request and settings,
Continue aborts/stops only after confirmation, and EN/AR headings track the rate.
No real video decoder, camera, detector, training export or backend is used.

The map regression uses legacy and new-contract synthetic report sets (22/40 reports), including manual/device-GPS,
overlapping, missing, invalid, unknown-source, simulated and zero coordinates.
It covers English/Arabic at 1440, 390 and 320 pixels, location groups, pagination,
map search/status filters and paging independent of Review queue, empty results, keyboard pin/list
selection, report opening, direct map help and repeated focus return. It asserts
no external requests or writes. See [map behavior and limits](MAP_GUIDE_CLARITY.md).
