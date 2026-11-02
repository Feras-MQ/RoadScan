# Street-map first version

This is an unmerged development feature. The submitted deliverables and running demo are not changed by this branch.

## Behavior and boundaries

The coordinate diagram and paged report list remain local. Street tiles are off by default, and consent is not saved across screen visits or location groups. **Load street map** first fetches bounded local pin metadata. Only a successful, nonempty, valid response causes the locally bundled Leaflet module to request tiles. API failure, invalid responses, tile errors and initial tile timeout restore the diagram/list. There is no automatic retry. Turning the layer off or leaving the screen removes it and cancels pending pin loads.

The notice identifies the tile host and explains that it receives the viewer's IP, site origin and viewed region. Tile image elements use `referrerPolicy="origin"`; the app's other referrer/security policies are unchanged. Browser image loading honors normal HTTP caching; the app adds no no-cache headers, prefetch, offline download, retina requests or extra tile buffer. Zoom is bounded and tiles update after movement ends. Visible OSM attribution stays on the map, including mobile/RTL layouts. Leaflet's BSD license ships as `/leaflet-license.txt`.

Default tiles: `https://tile.openstreetmap.org/{z}/{x}/{y}.png`. A build may set `VITE_OSM_TILE_URL` to another **OSM-derived** HTTPS XYZ tile endpoint with appropriate usage permission. The displayed destination updates to its host. Credentials, query strings and fragments are rejected; this feature supplies no paid API integration or key management. OSM attribution remains required. Changing a provider requires checking that provider's terms and caching requirements separately.

Recorded and simulated requests never mix. Simulated pins have dashed square markers and explicit labels, and no outbound location links. Pin colours describe review status, not severity. Coincident pins remain separately selectable in the numbered selector. Valid polar coordinates outside Web Mercator's latitude range are omitted only from street rendering, with a notice; their stored values and coordinate-diagram/list access are unchanged. Coordinates are never moved, jittered, invented, extracted from EXIF or collected from the browser.

The street selection has one dedicated detail card and uses the existing guarded report-opening callback. The old list inspector is hidden while the street layer is active. Selecting a list row turns the street layer off and returns focus to the local inspector. List pagination is independent of the compact street-pin layer.

## Backend contract

Contract agreed in [PR #1 comment 6573345086](https://github.com/Feras-MQ/RoadScan/pull/1#issuecomment-6573345086), implemented separately by [PR #9](https://github.com/Feras-MQ/RoadScan/pull/9).

`GET /api/reports/map`: existing read authentication; `location=recorded|simulated` required, optional exact review `status`, `damage=D00|D10|D20|D40|OTHER|none`, `limit=2000`. Response `{items,total,returned,limit,truncated}`, with compact fields `{id,latitude,longitude,location_source,status,score,classes,created_at}`. `created_at` may be null. The frontend validates count consistency, cap, coordinates and provenance before drawing. It shows returned/total/limit and a truncation warning rather than claiming complete coverage.

The endpoint does **not** support text search. Entering a report search turns street pins off; a visible explanation asks the user to clear it before reloading. The existing searchable paged list/diagram remains functional. The damage-class selector explicitly applies to street pins only. Empty detection results are not proof of a damage-free road.

An older backend gives an honest unavailable/fallback state, with no tile request. Backend PR #9 must land with or before this feature for compact pins to work. The API's cap bounds response size; its current Python filtering scans matching detections, so it is not a backend memory bound.

## External links

Recorded coordinates may open Google Maps or Street View in a new tab **only when the user clicks**. The disclosure identifies Google, location sharing, nearby/absent/outdated panoramas, and that street imagery is not current damage evidence. No embedding, imagery lookup, billing, API key or inferred camera heading is included. There is no assumption about coverage in any country.

## Verification

Build with `npm run build`, run units with `npm test`, and run `node tests/street-map.runner.mjs` with the documented existing Playwright/Chrome environment variables used by `website-guide.browser.mjs`. The runner uses an ephemeral localhost server, synthetic reports and intercepted synthetic tiles. It never sends real/private coordinates to a provider or contacts the running app. `ROADSCAN_MAP_TEST=street` runs just the new layer matrix; without it the prior map regression matrix runs too. Full `website-guide.browser.mjs` also includes these new checks.

Browser coverage includes EN/AR desktop/mobile; zero pin/tile requests before opt-in; origin-only referrer and absent API token on tile requests; keyboard activation; attribution; overlapping/off-page pins; no-detections filter; simulated/missing/polar coordinates; text-search fallback; unavailable/invalid API response; tile error/retry; cancel during pending pins; 2,000/2,001 truncation; report navigation; layout and focus. Tests render synthetic tiles and do not establish live OSM availability, a service guarantee or real Google panorama coverage.

Provider sources checked 2 November 2026:

- [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/)
- [Leaflet 1.9.4 API reference](https://leafletjs.com/reference.html)
- [Google Maps URLs / Street View](https://developers.google.com/maps/documentation/urls/get-started#street-view-action)
