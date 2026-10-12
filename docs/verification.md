# Implementation verification

Checked 11 October 2026 using the pinned Vega 5.33.0, Vega-Lite 5.23.0 and Vega-Embed 6.29.0 browser runtimes.

## Completed checks

- All twelve JSON specifications compile (where applicable), parse, run, and serialize to SVG with the local Vega runtime. The browser renders all twelve without reported chart errors.
- A real browser loaded the complete single-page website and every chart. Console error/warning inspection returned no messages during the initial load and filter tests.
- At a normal desktop viewport, all charts and four sections were visually inspected. At a 390 px viewport override (375 px content area after the scrollbar), the document's scroll width equalled its client width. All twelve rendered SVGs fit their containers. A 1366 px desktop override was also exercised.
- Price = Budget gives four matching records, four mapped points, four scatter points and four shortlist points.
- Budget + minimum 4,000 reviews gives zero matching records with an explicit status message; it does not leave the previous restaurant points visible.
- Vegan options gives 25 matching records, including 22 mappable records.
- A real pointer drag over the scatterplot selected 13 records in the test rectangle, narrowed the map to 11 matched coordinates and produced a top-ten shortlist, while retaining all 31 points in the scatterplot for context.
- Changing the price filter after brushing cleared the brush and consistently updated all three charts. Reset restored 31 matching records and 27 mapped points.
- Source statistics, exclusive dietary intersections, geographic counts and coordinate joins were independently checked; see [source-audit.md](source-audit.md).

## Public deployment

GitHub Pages was enabled on 11 October 2026 from the `main` branch and repository root. The first website commit was `58ff0fcc0f842fd046937bbcf23c4e0e4dfee6fa`.

The public URL, https://markkongsama.github.io/fit3179-restaurant-reviews/ , returned HTTP 200. A fresh browser loaded all twelve charts, with no error/warning log entries. The empty-result filter was tested again on the public site. At a 390 px viewport override, client width and scroll width both measured 375 px and all twelve SVGs fitted their containers. Original full-page desktop and mobile screenshots are saved with the local report.

## Limits of this verification

The desktop and phone checks cover the observed browser, sizes and scenarios, not every browser, assistive technology or device. No marks or grade are guaranteed by chart counts. The actual hand-drawn sketch has been reported complete by the author but its image has not been supplied for visual comparison. The report therefore remains a draft until the original sketch, student ID, studio details and final author review are added. No Moodle submission has been made.

## Current publication status

GitHub Pages was temporarily disabled on 11 October 2026 at the author's request (DELETE 204; subsequent GET 404). On 12 October 2026, the author confirmed they were using the public site, and the existing public page was observed in the browser. Publication is active again.

## Data access repair — 12 October 2026

The four original download links exposed JSON/GeoJSON directly, and the methods link exposed Markdown. They now open searchable data previews and a readable HTML methods page. Each preview offers an Excel-friendly CSV download and retains the original data format as a separate option.

- CSV exports contain 31 review records, 1,645 venue records, 13 areas and 87 occupied grid cells. The exporter reopens each output and checks every field, including full geometry, against the source records. CSV uses UTF-8 BOM; arrays use semicolons, nulls become empty cells, and formula-like text receives a protective apostrophe. Negative numeric coordinates are unchanged.
- Browser checks covered all four previews, pagination, a restaurant search, an empty search and clearing the search back to 31 records. A real browser download of `reviews.csv` was reopened and confirmed to contain the expected 31 records.
- At a 390 px viewport override, the data page uses the mobile card layout. The data page and methods page both had a document scroll width equal to client width (375 px).
- The HTML methods page preserves all six source sections and all 31 location-crosswalk rows. Local links from the main page, data page and methods page resolve to existing files.
- Chart specifications, chart interaction code and the JSON/GeoJSON files used by the charts are unchanged by this repair. The narrative and its twelve charts remain on the original single page; the extra pages provide supporting data and methods.
