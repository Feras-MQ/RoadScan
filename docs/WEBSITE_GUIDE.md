# Website guide

The **Website guide / دليل الموقع** button opens a bilingual help panel on every
screen, including before connection. It offers common topics, suggestions for the
current screen, and short typed questions matched to curated instructions. Matching
normalizes common English articles/possessives and Arabic articles/diacritics.
Specific phrases consume their generic words (for example, "upload video"), while
separate conflicting intents still fall back instead of guessing. It is
not an LLM, report explainer, or command executor. Questions are kept in component
memory and cleared when the panel closes. The guide receives only language,
screen, whether a report is selected, and a navigation callback.

Topics cover photo upload, model voting, detection editing, video analysis,
saving reviews, report export availability, training-data download, map use,
settings, and common errors. There is no website PDF/CSV report-export control in
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
blocks leaving an unsaved review or an App-level
busy task. The existing report-switch guard remains in place. Leaving a selected
report asks for confirmation because its model-vote job/results/choices and
training fields live in child components, outside the review-dirty flag. Cancel
keeps those components mounted and their work intact; Continue intentionally
unmounts them, cancelling a running vote and discarding their local state. This
guard also asks for a selected report with no child work in progress. Leaving Live
recognition, Settings, or Learning asks for confirmation because child workflows
can stop or lose selections on unmount. This is conservative: it also asks when
those screens are idle. Clicking the current screen is a no-op that preserves
local state without prompting; idle Overview/Map transitions need no confirmation.
Explicit workflow handoffs (opening a report or using a captured frame) retain
their existing behavior. Browser-history routing is not implemented.

The full-video heading and intro reflect the selected sampling rate in both
languages. The every-frame wording appears only for the Every frame option.

## Verification

From `frontend` with the project's existing dependencies:

```sh
node --test tests/*.test.ts
node node_modules/typescript/bin/tsc --noEmit -p tsconfig.json
node node_modules/vite/bin/vite.js build
node tests/website-guide.browser.mjs
```

The browser check needs an **already installed** Playwright package and Chrome.
If Playwright is outside normal module resolution, set
`ROADSCAN_PLAYWRIGHT_MODULE` to its `index.mjs` file URL and
`ROADSCAN_PLAYWRIGHT_EXPECT` to its `test.mjs` file URL. Optionally set
`ROADSCAN_CHROME` to an existing Chrome executable and `ROADSCAN_QA_OUTPUT` to a
screenshot output directory. It does not install anything.

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
