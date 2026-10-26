# RoadScan design and workflow update

Release 2026-10-27.1 keeps the road-scanning visual identity and makes reviewing an inspection easier to follow.

## Use the review screen

1. Open a report. Its image and review controls receive focus automatically, including on a phone.
2. Use **Inspect image** and **Check boxes** to examine the evidence.
3. Choose **Save decision** to reach the status, note and save controls directly.

Optional model voting, nearby matching and training approval remain available below the decision. A saved review does not automatically train a model. Notes, status changes and annotation edits all show an unsaved indicator; opening another report still asks before discarding them.

A failed photo now has **Retry image**, which preserves the draft. A failed workspace refresh has **Retry connection**. Loading, disconnected and empty search results have distinct messages; **Clear filters** restores the queue. Queue numbers explicitly say they are draft scores out of 100, not measured damage severity.

## Design decisions and sources

The existing navy surfaces, lime primary action, cyan navigation and warm warning color are retained. Review steps represent a real sequence; optional checks are separated from saving. Existing fonts and Lucide icons are reused. Motion remains optional, image coordinates remain fixed, controls retain visible focus, and layouts support English and Arabic direction.

- [Taste Skill app guidance](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/references/app-screens.md): calm working surfaces, clear selection and compact phone layouts; [MIT license](https://github.com/Leonxlnx/taste-skill/blob/main/LICENSE).
- [UI UX reference](https://devanshutak25.github.io/ui-ux-ref/index.html): explicit feedback and usable form states; [MIT license](https://github.com/devanshutak25/ui-ux-ref/blob/main/LICENSE).
- [Vercel interface guidance](https://github.com/vercel-labs/web-interface-guidelines/blob/main/command.md): skip links, focus, actionable errors and reduced motion; [MIT license](https://github.com/vercel-labs/web-interface-guidelines/blob/main/LICENSE).
- [Anthropic frontend design guidance](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md): subject-specific design and restrained surrounding controls; [Apache 2.0 license](https://github.com/anthropics/skills/blob/main/skills/frontend-design/LICENSE.txt).
- [VIBE DESIGN](https://d.playwithai.fun/): reviewed as an inspiration gallery; no clear license was found on the inspected landing page, so no code or assets were copied.

These are design references, not installed dependencies. No external workflow, browser script, font, tracker or animation package was added.

## Verification and limits

The full isolated backend suite passed **221 tests**, with **1 optional sklearn skip**; **24 frontend tests** passed and the production build succeeded. Browser verification covered **17 interaction checks**, **40 English/Arabic screen-width cases** across five screens at 320, 390, 860 and 1440 CSS pixels, and **10 final narrow-screen rechecks**. The image-reader correction also passed 17 focused backend checks with the detector configured. Missing or corrupt photos return structured errors without saving a changed report.

Browser fixtures are synthetic. These checks do not measure detector accuracy, validate Saudi field performance, test physical camera/drone hardware, or establish fresh Mac/ARM compatibility. Genuine labeled Saudi photos, repeated-damage pairs and original split/provenance evidence are still outstanding. Word pagination remains unverified; the checked PDF is the presentation copy.
