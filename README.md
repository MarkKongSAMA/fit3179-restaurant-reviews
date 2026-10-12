# Beyond the Stars — Melbourne Restaurant Reviews

A single-page data story by **Runmin Kong** for FIT3179 Data Visualisation 2.

The website explores the 2024 City of Melbourne dining landscape alongside **31 selected Tripadvisor listings accessed on 6 October 2026**. The sample is non-random, is not representative of the city, and includes no review prose or photographs. Access dates do not establish that cached reader snapshots were refreshed on that date.

## Run locally

Serve this folder with a static web server, then open its local address. For example:

```sh
python -m http.server 8766 --bind 127.0.0.1
```

Open `http://127.0.0.1:8766/`. The port is a local preview setting, not an assignment requirement; if you choose another free port, use the same number in the command and browser address. Directly opening `index.html` as a file can block data requests.

URL for publication: https://markkongsama.github.io/fit3179-restaurant-reviews/

## Structure

- `index.html`, `styles.css`, `app.js`: editorial page, responsive layout and shared interactions.
- `specs/`: twelve readable Vega / Vega-Lite JSON specifications, linked beside each chart.
- `data/processed/`: downloadable chart-ready data and geography.
- `data/raw/`: preserved source extracts and source metadata used by the preparation script.
- `scripts/prepare_data.py`: deterministic cleaning, location crosswalk, UTM grid and validation assertions; Python standard library only.
- `scripts/build_specs.py`: reproducible chart specification generation.
- `docs/data-quality.md`: grain, geographic methods, record joins and interpretation limits.
- `vendor/`: pinned browser runtimes. Vega 5.33.0, Vega-Lite 5.23.0, Vega-Embed 6.29.0 (BSD-3-Clause; upstream notices retained in `vendor/LICENSES.txt`).

## Twelve visualisations

| No. | Chart | Purpose |
|---|---|---|
| 01 | Choropleth | Official venues per km² by CLUE small area |
| 02 | Proportional symbol map | Review count by circle area, rating by colour |
| 03 | Bin map | Official counts in equal 500 × 500 m UTM squares |
| 04 | Histogram | Rating distribution at the recorded 0.1 resolution |
| 05 | Scatterplot | Rating and lifetime review count; linked interval selection |
| 06 | Boxplot with points | Rating distributions by ordinal price band |
| 07 | Heatmap | Multi-label cuisine tags versus price, including zero cells |
| 08 | Bar chart | Number of listings carrying each dietary tag |
| 09 | Waffle / unit chart | 31 whole cells, one per sample listing |
| 10 | Treemap | Price band → restaurant hierarchy, area by review count |
| 11 | Venn diagram | Exact dietary-tag intersections; schematic circle areas |
| 12 | Ranked dot plot | Up to ten matching sample listings, with explicit tie rule |

Price, minimum review count and dietary-tag controls update 02, 05 and 12 and the listing table. Brushing 05 additionally filters 02 and 12; reset clears both controls and brush. All other charts retain the full sample or official context, as labelled.

## Data and attribution

City of Melbourne: [Café, restaurant, bistro seats](https://data.melbourne.vic.gov.au/explore/dataset/cafes-and-restaurants-with-seating-capacity/) and [CLUE small areas](https://data.melbourne.vic.gov.au/explore/dataset/small-areas-for-census-of-land-use-and-employment-clue/), licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Latest available census year verified as 2024 on 11 October 2026. Indoor/outdoor seating rows aggregate to 1,645 establishment-location records after filtering ANZSIC 4511.

Tripadvisor: 31 attributed factual listing records, with individual source URLs in `reviews.json`. Twenty-five featured listings encountered on the Melbourne page plus six selected fine-dining listings form a convenience sample. No open-data licence is asserted for this material. Scores range from 4.1 to 4.8; cumulative review counts are not sales, annual visits, market share or confidence measures. Ordinal price symbols are not dollar prices; missing dietary tags mean unknown. Historical building coordinates match 27 records; four are withheld from the map only.

## AI acknowledgement

OpenAI Codex assisted with source research, chart and webpage implementation, and explanatory writing. Runmin Kong is responsible for reviewing the outputs, checking the original sources, debug the submitted design and code.