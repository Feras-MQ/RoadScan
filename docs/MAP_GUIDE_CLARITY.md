# Map and guide clarity — 1 November 2026

**Map & results** helps find a saved report by its saved location, then open the
image for human review. Its coordinate diagram has no street tiles, routing or
distance scale. Positions fit the current page, so changing pages or filters can
move pins. It is not a geographic survey or a severity map.

The map owns its search, review-status filter and pagination independently of
Review queue. With the additive map API, location groups page through the whole
workspace. Group counts come from `stats.by_location` and are explicitly before
search/status filters; result totals reflect those filters. On older servers
without complete valid location counts, the map loads ordinary report pages and
labels its location counts and groups as **Limited coverage: this loaded page
only**. It never presents this fallback as all located reports. The groups are:

- **Recorded locations:** valid coordinates with a manual or reported device-GPS
  source. Neither source is independently verified.
- **No usable location:** missing/invalid coordinates or unspecified/unknown
  provenance. Reports remain selectable for image review without invented pins.
- **Simulated locations:** explicitly marked demonstration positions, kept
  separate from recorded positions. Missing/invalid coordinates are never plotted;
  their records remain reviewable. Every server-returned row remains in the list
  even if its coordinates or source cannot safely produce a pin.

Numbered pins correspond to list entries. Overlapping positions are not displaced;
the list provides access to every report. Selection color has no severity meaning.
The inspector shows the image, review status, saved-box count, coordinate pair and
source. The former draft-priority display is omitted here to avoid implying that
location or selection establishes severity. **Open image & review** uses the
existing report-opening and unsaved-review protection.

No external map is loaded. The existing Google Maps link appears only for valid
manual/device-GPS coordinates and now explicitly explains that opening it shares
those coordinates with Google. There is no external link for simulation or unknown
provenance. The test suite never opens that link.

For one new photo, **Overview → New inspection → Browse files → Add location
(optional)** accepts latitude/longitude and Manual or Simulated demo provenance.
The map does not collect GPS, extract it from photos/video frames or edit existing coordinates.
Empty states explain what is missing and offer another location group, filters,
page navigation or a new inspection as appropriate.

**How this map works** opens the curated bilingual guide directly. The guide also
answers basic missing-pin/GPS questions and offers **Add a location to a new
photo**, with explicit user-click navigation to Overview. It reads no report data,
does not infer coordinates and does not perform uploads, inference or writes.
Existing guard behavior is unchanged. All copy and controls have Arabic/English
equivalents, and keyboard selection moves focus to report details with a way back
to the list.

## Verification and scope

Run the frontend unit tests, TypeScript check, Vite build and
`node tests/website-guide.browser.mjs` as described in
[the guide verification instructions](WEBSITE_GUIDE.md#verification).

The added browser scenarios use only synthetic API fixtures in isolated browser
contexts: legacy page-only fixtures and the new API contract (22/40 reports), valid/invalid/unknown/simulated locations,
overlaps, zero coordinates, independent map/review paging and filters, empty results, keyboard selection,
guide focus/close/reopen, navigation and unsaved review protection in English and
Arabic at desktop and narrow mobile widths. Existing model-vote/training/video
navigation guard scenarios remain part of the suite. The fixture server rejects
writes, and browser contexts block external network access.

This change introduces no dependencies, backend edits, model changes, report
migrations, map service credentials or video-asset changes. Browser fixtures do
not establish real GPS accuracy, field usability, detector accuracy, a fresh
installation or deployment. The older dated interface screenshots remain a
historical snapshot; they do not show this redesign.

The frontend recognizes the additive contract proposed in PR #4: optional
`location=recorded|simulated|none` on `/api/reports`, and nonnegative integer
`by_location` counts summing to the workspace total on `/api/stats`. This frontend
branch does not include or merge that backend PR. New-contract browser responses
are mocked; combined real-backend verification remains an integration check.

Local verification for this frontend change: 42 frontend unit tests passed;
TypeScript and Vite production build passed. The complete synthetic browser suite
passed its base guide checks, 12 existing report/video navigation guard scenarios,
and 12 map scenarios (legacy/new contract × English/Arabic × 1440/390/320 px).
Additional new-contract checks covered an invalid returned row, conflicting
coverage totals and navigation during a delayed request. Request failure/retry
was checked in every map scenario. No backend code changed or backend tests were
rerun for this frontend-only branch; real combined-API verification is pending.

Guide matching also recognizes the exact location-group labels in both languages
and video-report location questions. Compound phrases consume their generic video
and map words; independent mixed intents still fall back rather than guessing.
