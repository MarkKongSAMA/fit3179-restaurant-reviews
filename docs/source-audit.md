# Source and computation audit — 11 October 2026

This bounded audit verifies provenance and calculations while retaining the 6 October 2026 review snapshot. It does not collect a new sample or assert that every restaurant listing is current.

## Official data freshness

A direct City of Melbourne API `max(census_year)` query returned `2024-01-01T00:00:00+00:00`: **2024 remains the latest available year in this dataset on the audit date.** The response and current metadata are saved in `data/raw/source-audit-2026-10-11.json`. The API was read directly after the web reader could not open the API endpoints.

- [Maximum census year query](https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/cafes-and-restaurants-with-seating-capacity/records?select=max%28census_year%29&limit=1)
- [Seating dataset metadata](https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/cafes-and-restaurants-with-seating-capacity): data processed 16 March 2026; metadata processed 3 September 2026; coverage 2002–2024.
- [CLUE area metadata](https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/small-areas-for-census-of-land-use-and-employment-clue): data processed 13 November 2022; metadata processed 3 September 2026.

Processing dates and census year are different. A newer metadata date does not mean that businesses or boundaries were surveyed that day. Both government datasets retain their CC BY 4.0 licence. The newly read timestamps agree with the saved original metadata.

## Review spot checks

Original restaurant listing pages were read on 11 October. Ratings, review counts, price symbols, addresses, cuisine arrays, and recorded diet tags match the preserved snapshot for each of these three listings:

| Listing | Rating | Cumulative reviews | Source |
|---|---:|---:|---|
| Rice Paper Scissors | 4.6 | 3,058 | [Tripadvisor listing](https://www.tripadvisor.com.au/Restaurant_Review-g255100-d5539081-Reviews-Rice_Paper_Scissors-Melbourne_Victoria.html) |
| The Hardware Societe | 4.5 | 1,903 | [Tripadvisor listing](https://www.tripadvisor.com.au/Restaurant_Review-g255100-d1971945-Reviews-The_Hardware_Societe-Melbourne_Victoria.html) |
| Hakata Gensuke Ramen | 4.4 | 377 | [Tripadvisor listing](https://www.tripadvisor.com.au/Restaurant_Review-g255100-d7079347-Reviews-Hakata_Gensuke_Ramen-Melbourne_Victoria.html) |

The reader reports a recent crawl, but this is not proof of the source data update time. The rest of the31 listings were not refreshed in this bounded audit. Keep the visible review access date as **6 October 2026**, and describe the values as a saved snapshot. Hakata Gensuke has no Special Diets tags in the read listing metadata; this means none recorded, not that dietary options are unavailable. The three checks found no demonstrated error requiring a snapshot correction.

## Independent reconciliation

Checks run directly against saved raw and processed JSON confirmed:

- All 3,249 raw census records concern 2024. There are 2,435 ANZSIC 4511 seating rows, representing 1,645 unique property ID + trading name + business address records.
- Indoor/outdoor seat sums reconcile exactly to 130,223; no source row is duplicated and no seating type repeats within a grouped establishment.
- Each derived venue agrees with its source grain and seat sum. All 1,645 venue coordinates fall inside their source-assigned CLUE area polygon in an independent point-in-polygon check.
- The 13 area counts and 87 occupied 500 m grid counts both sum to 1,645. Density is venue count divided by projected polygon area in km²; zero-count areas remain present.
- All31 review names, ratings, counts, URLs, and access dates agree with the raw snapshot; cuisine/diet arrays are faithful comma-splits without duplicated tags. Three previously documented address completions remain explicit in the preparation script.
- All 27 mapped listings resolve to exactly one designated CLUE record and copy its coordinates, address and area. All 4 unmatched records have null coordinates and area. There is no review-to-venue one-to-many expansion.
- The script projection round-trip maximum error is 3.15e-10 degrees; projected polygon areas agree with official shape_area within 0.001321%.

The Railway Club Hotel status was made more precise: `unmatched_no_clue_match` records that its name/address could not be matched in the saved extract. Lack of a match alone is not treated as proof of a geographical boundary. Grill Steak Seafood, Il Solito Posto and Flower Drum retain unresolved address differences and remain excluded from the review map.

## Exact statistics for narrative and chart QA

| Metric | Verified value |
|---|---:|
| Recorded café/restaurant locations | 1,645 |
| Melbourne (CBD) locations | 953 (57.93% of the 1,645) |
| Melbourne (CBD) density | 383.361 locations/km² |
| Review sample / mapped sample | 31 / 27 |
| Total cumulative review counts across sample | 39,882 |
| Sample rating range / median | 4.1–4.8 / 4.5 |
| Review count range / median | 233–6,156 / 1,083 |
| Price counts: Budget / Mid-range / Premium | 4 / 20 / 7 |
| Rating median within each price band | 4.5 / 4.5 / 4.5 |
| Top 5 listings share of all recorded review counts | 40.063% |
| Listings with multiple cuisine tags | 30 of 31 |
| Cuisine tag occurrences / distinct labels | 100 / 36 |

A cuisine count can exceed the sample denominator when summed because one listing can have several labels. The first source-listed tag is not a verified primary cuisine. Cumulative review volume is not restaurant capacity, footfall or a confidence interval.

## Dietary set audit

| Exact recorded-label region | Count |
|---|---:|
| Vegetarian + vegan + gluten-free | 23 |
| Vegetarian + vegan, without gluten-free recorded | 2 |
| Vegetarian + gluten-free, without vegan recorded | 3 |
| Vegetarian only | 1 |
| Gluten-free only | 1 |
| Vegan only | 0 |
| Vegan + gluten-free, without vegetarian recorded | 0 |
| None of the three labels recorded | 1 |
| Total | 31 |

Inclusive totals are vegetarian 29, vegan 25, gluten-free 27. Inclusive pair intersections are vegetarian–vegan 25, vegetarian–gluten-free 26, vegan–gluten-free 23. Every vegan-tagged listing in the saved sample is also vegetarian-tagged. A set diagram must preserve that containment or clearly mark zero regions; drawn circle areas must not be presented as proportional if they are schematic. Dietary labels require checking with restaurants for individual needs.

## Source file fingerprints

SHA-256 fingerprints allow a reviewer to verify the retained inputs. The three restaurant spot checks did not modify them.

| Original input | SHA-256 |
|---|---|
| `clue2024.json` | `09c14fb9a6861e6f2a11b83e8d6a8359a4293f983b56857f93409c4ee1a6d1ad` |
| `review_metadata.json` | `3d2fea05f7d0bf46b327899603e562c8d11d5250f62ae714b2afd924a87125b2` |
| `small_areas.geojson` | `831a60ed96958e7ba203601372192eeba13b7ad25bf06e41810c031df95d6339` |
| `cafes-and-restaurants-with-seating-capacity-metadata.json` | `859f3dfb30b14ddfc10e39e4b217078bfd4b463b5631c9a53f2a411ad477d049` |
| `small-areas-for-census-of-land-use-and-employment-clue-metadata.json` | `1b9f14d3e1d9eafbfeba5e4d90457614b74065710ca51993ecd70210c0537d7f` |

Scope limits remain: a non-random 31-listing convenience sample, self-reported platform tags, different census/review periods, historical building-level coordinates, no review text analysis and no city-wide quality estimate.
