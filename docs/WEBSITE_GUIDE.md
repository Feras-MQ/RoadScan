# Website guide

The **Website guide / دليل الموقع** button opens a bilingual help panel on every
screen, including before connection. It offers common topics, suggestions for the
current screen, and short typed questions matched to curated instructions. It is
not an LLM, report explainer, or command executor. Questions are kept in component
memory and cleared when the panel closes. The guide receives only language,
screen, whether a report is selected, and a navigation callback.

Topics cover photo upload, model voting, detection editing, video analysis,
saving reviews, export availability, map use, settings, and common errors. There
is no website report-export control in this baseline, and the export answer says
so. Instructions and both languages live in `frontend/src/guideContent.ts`;
update them when the actual UI labels or workflows change.

**Open this screen** uses an allowlisted topic destination and the existing screen
state. It never starts a camera, uploads media, selects models, saves a review, or
changes a permission. When a report is needed but none is selected, it opens the
review queue and asks the user to select one. A temporary outline and keyboard
focus point to the relevant panel; it clears after eight seconds, navigation,
dismissal, or reopening the guide. The modal supports Escape, a sticky Close
button, focus containment/return, and Arabic RTL.

Navigation through the guide blocks leaving an unsaved review or an App-level
busy task. The existing report-switch guard remains in place. Leaving Live
recognition, Settings, or Learning asks for confirmation because child workflows
can stop or lose selections on unmount. This is conservative: it also asks when
those screens are idle. The guide does not change the existing sidebar navigation
or implement browser-history routing.

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
requests, rejects API writes, and closes the browser/server afterward. It checks
English/Arabic at desktop and mobile sizes, typing/fallback, destinations,
keyboard/close/reopen, highlight cleanup, unsaved review guards, retained photo
selection, and disconnected help. It does not run real detector inference or
read actual report storage.
