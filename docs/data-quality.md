# Data quality and reproducibility

Checked: 2026-10-06. Reproduce with `python scripts/prepare_data.py` from the project directory.

## Grain and checks

The saved 2024 CLUE extract contains 3,249 rows across multiple industries. Filtering ANZSIC 4511 (Cafes and Restaurants) leaves 2,435 seating rows. Summing indoor and outdoor seats by property ID + trading name + business address yields **1,645 establishment-location records** and 130,223 seats. Different property/address records are not merged just because they have the same trading name. This is an operational venue count, not a count of brands.

No exact duplicate source rows, repeated seating types within an establishment, conflicting within-establishment coordinates/areas, missing venue coordinates, or invalid rating/review-count values were found. All area and grid counts reconcile to the venue total. Assertions in the preparation script stop processing if those conditions change.

## Geography

Polygon areas and 500 × 500 m cells use WGS84 / UTM zone 55 south (EPSG:32755), implemented using the standard transverse-Mercator series. Cells are aligned to multiples of 500 m in UTM eastings/northings. Only occupied cells are exported. Cells are not clipped to municipal boundaries: clipping would destroy the equal-area interpretation. Areas are projected surface areas, not ground-survey measurements.

Forward/inverse round-trip error across all venue coordinates is at most 3.15e-10 degrees. Computed polygon area differs from the official `shape_area` by at most 0.001320%. This independent metadata comparison checks the units and projection implementation. The source boundary coordinate reference is interpreted as WGS84 longitude/latitude as served in GeoJSON. Exterior rings are rewound clockwise for Vega/D3; holes counterclockwise.

Small areas are CLUE statistical areas and do not exactly equal suburbs or postcodes. Density uses the full polygon area, including parks, industrial land and water. The source's area assignment is used for venue counts; no new boundary reassignment is inferred.

## Review sample and freshness

The 31 records are a convenience sample: 25 featured listings encountered on the Melbourne restaurant page plus six selected fine-dining listings. Selection was not random, exhaustive, or a reproducible city-wide rank sample. The sample contains only ratings from 4.1 to 4.8 and cannot estimate average Melbourne restaurant quality or establish a price/cuisine effect. Treat small cells and comparisons as descriptions of these listings only.

Each record retains its source URL and access date. Web-reader pages may be cached: 6 October 2026 is an access date, not proof that all figures were refreshed that day. Review counts accumulate over each listing's lifetime. No annual time series, review text, sentiment, confidence intervals, actual meal prices or independent dietary verification are available.

Price labels map `$` to Budget, `$$ - $$$` to Mid-range, and `$$$$` to Premium. These are ordinal bands. `primary_cuisine` is only the first listed cuisine tag, retained deterministically for grouping; labels such as Asian and International are broad platform tags, not a verified hierarchy. Cuisine and diet arrays retain all listed tags. Absent dietary flags are null (unknown), never false.

The dietary overlap chart describes recorded labels. Of 31 listings, 23 record all three labels, two record vegetarian + vegan only, three record vegetarian + gluten-free only, one records vegetarian only, one records gluten-free only, and one has none recorded. Vegan-only and vegan + gluten-free without vegetarian both contain zero listings. Thus every vegan-tagged listing in this sample is also vegetarian-tagged. These set relationships describe the saved listing labels, not independently verified menus. In `summary.json`'s derived overlap regions, false means a tag was not recorded.

The raw file had three missing addresses. The existing Tripadvisor source URLs were reread on 6 October 2026: Hardware Societe lists 10 Katherine Pl; Movida lists 1 Hosier Lane; Da Guido 365 lists 365 Little Collins St. Corrections are explicit in the script; the raw file remains untouched. One restaurant, Hakata Gensuke, has no saved dietary tags.

## Joining locations

**27 of 31** listings have an explicit name/address crosswalk to 2024 CLUE. Coordinates are building-level historical locations. Four listings remain unmapped; all 31 remain in non-spatial sample charts. A matched coordinate does not establish that the business is still open in 2026. The source review address and matched CLUE address are both retained. Review ratings are never copied to all venues in an area.

| Listing | Status | Review address | CLUE address | Join note |
|---|---|---|---|---|
| Rice Paper Scissors | matched_building | 15 Hardware Lane, Melbourne, Victoria 3000 Australia | Ground 13-15 Hardware Lane MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Hochi Mama | matched_building | 35 Little Bourke St, Melbourne, Victoria 3000 Australia | Ground 35 Little Bourke Street MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Brick Lane Melbourne | matched_building | 33 Guildford Lane, Melbourne, Victoria 3000 Australia | Ground 33 Guildford Lane MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Straight Outta Saigon | matched_building | 138 Russell Street Ground level, Melbourne, Victoria 3000 Australia | Ground 138-144 Russell Street MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Da Guido La Pasta | matched_building | 130 Lygon St Carlton, Melbourne, Victoria 3053 Australia | 128-130 Lygon Street CARLTON VIC 3053 | Name/alias and street address agree with 2024 CLUE. |
| Foglia di Fico | matched_building | 585 La Trobe St (Spencer St entrance), Melbourne, Victoria 3000 Australia | Restaurant 585 La Trobe Street MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Grill Steak Seafood | unmatched_address_difference | 68 - 68 Hardware Lane, Melbourne, Victoria 3000 Australia | — | Source 68 Hardware Lane versus CLUE 66; possible address expansion. Coordinate withheld pending verification. |
| 11 Inch Pizza | matched_building | Shop 7A 353 Little Collins St, Melbourne, Victoria 3000 Australia | Shop 6B, 353 Little Collins Street MELBOURNE VIC 3000 | Same building and exact name; source shop 7A versus CLUE shop 6B. Building-level location only. |
| Waterfront | matched_building | 3 Southgate Avenue Southgate Precinct, Shop 20, Melbourne, Victoria 3006 Australia | Shop 20, Ground 3 Southgate Avenue SOUTHBANK VIC 3006 | Name/alias and street address agree with 2024 CLUE. |
| The Meat & Wine Co Southbank | matched_building | Freshwater Place 3 Queensbridge Street, Melbourne, Victoria 3006 Australia | Shop 2R, 3 Freshwater Place SOUTHBANK VIC 3006 | Source names Freshwater Place and 3 Queensbridge Street; CLUE names 3 Freshwater Place. Building-level location. |
| The Hardware Societe | matched_building | 10 Katherine Pl, Melbourne, Victoria 3000 Australia | 10 Katherine Place MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Roule Galette Melbourne | matched_building | 241 Flinders Lane Shop 1, Melbourne, Victoria 3000 Australia | Shop 1B, 241 Flinders Lane MELBOURNE VIC 3000 | Same 241 Flinders Lane building; source shop 1 versus CLUE shop 1B. |
| Supernormal | matched_building | 180 Flinders Lane, Melbourne, Victoria 3000 Australia | 180 Flinders Lane MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Movida Bar de Tapas | matched_building | 1 Hosier Lane, Melbourne, Victoria 3000 Australia | Shop 5, 1 Hosier Lane MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| The Railway Club Hotel Steakhouse | unmatched_no_clue_match | 107 Raglan St, Melbourne, Victoria 3207 Australia | — | No matching establishment was found for 107 Raglan Street, Port Melbourne in the saved CLUE extract; no coordinate inferred. |
| Il Solito Posto | unmatched_address_difference | Basement/113 Collins St via George Parade, Melbourne, Victoria 3000 Australia | — | Source 113 Collins Street versus CLUE 111; possible entrance difference. Coordinate withheld pending verification. |
| Hofbrauhaus | matched_building | 18-26 Market Lane In the heart of Chinatown, Melbourne, Victoria 3000 Australia | Ground 18 Market Lane MELBOURNE VIC 3000 | Source street range 18-26 includes selected CLUE Ground 18; CLUE also records 26-28. One source listing plotted once. |
| Tipo 00 | matched_building | 361 Little Bourke St, Melbourne, Victoria 3000 Australia | Ground 361 Little Bourke Street MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Chin Chin | matched_building | 125 Flinders Lane, Melbourne, Victoria 3000 Australia | Gnd & Mezz 125 Flinders Lane MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Scopri | matched_building | 191 Nicholson St Carlton, Melbourne, Victoria 3053 Australia | 191 Nicholson Street CARLTON VIC 3053 | Name/alias and street address agree with 2024 CLUE. |
| Da Guido 365 | matched_building | 365 Little Collins St, Melbourne, Victoria 3000 Australia | Unit 1, Ground 365 Little Collins Street MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| El Rincon | matched_building | 69 Victoria Street Adjacent to the Queen Victoria Markets, Melbourne, Victoria 3000 Australia | 69 Victoria Street MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Stalactites Restaurant | matched_building | 177-183 Lonsdale St, Melbourne, Victoria 3000 Australia | 177-183 Lonsdale Street MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Shanghai Street | matched_building | 342 Little Bourke St, Melbourne, Victoria 3000 Australia | 342 Little Bourke Street MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Hakata Gensuke Ramen | matched_building | 168 Russell St, Melbourne, Victoria 3000 Australia | 168 Russell Street MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Vue De Monde | matched_building | 525 Collins St Rialto Building 55th Floor, Melbourne, Victoria 3000 Australia | Level 55S 525 Collins Street MELBOURNE VIC 3000 | CLUE combines Vue de monde and The Lui Bar on level 55. Coordinate only; combined seat count is not assigned to the review listing. |
| Il Bacaro Cucina e Bar | matched_building | 168-170 Little Collins St., Melbourne, Victoria 3000 Australia | 168-170 Little Collins Street MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Kazuki's | matched_building | 121 Lygon St Carlton, Melbourne, Victoria 3053 Australia | 121 Lygon Street CARLTON VIC 3053 | Name/alias and street address agree with 2024 CLUE. |
| Coda | matched_building | 141 Flinders Lane, Melbourne, Victoria 3000 Australia | Basement 141-143 Flinders Lane MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Maha | matched_building | 21 Bond St, Melbourne, Victoria 3000 Australia | Basement 21-27 Bond Street MELBOURNE VIC 3000 | Name/alias and street address agree with 2024 CLUE. |
| Flower Drum | unmatched_address_difference | 17 Market Lane, Melbourne, Victoria 3000 Australia | — | Source 17 Market Lane versus CLUE 124-128 Bourke Street; possible entrance difference. Coordinate withheld pending verification. |

Hofbrauhaus has two CLUE property records within the source street range; one building is selected and one review listing is plotted once. Vue de monde shares a CLUE record with The Lui Bar; no seat-count comparison is made at review-listing grain. Grill Steak Seafood, Il Solito Posto and Flower Drum have unresolved civic-address differences and are conservatively withheld from the map. The Railway Club Hotel's Raglan Street address is not matched in this municipal dataset.

## Source timing and reuse

- [Café, restaurant, bistro seats](https://data.melbourne.vic.gov.au/explore/dataset/cafes-and-restaurants-with-seating-capacity/) — City of Melbourne. Data processed 2026-03-16T21:21:12+00:00; metadata processed 2026-09-03T13:02:08.779000+00:00. CC BY 4.0
- [CLUE small areas](https://data.melbourne.vic.gov.au/explore/dataset/small-areas-for-census-of-land-use-and-employment-clue/) — City of Melbourne. Data processed 2022-11-13T10:18:37+00:00; metadata processed 2026-09-03T12:54:57.005000+00:00. CC BY 4.0
- [31 selected Melbourne restaurant listings](https://www.tripadvisor.com.au/Restaurants-g255100-Melbourne_Victoria.html) — Tripadvisor. Web-reader snapshot; individual pages may be cached. No open-data license asserted; factual listing metadata only, with per-listing attribution.

The 2024 census is the newest year present in the downloaded official dataset checked for this project. The 2026 processing timestamp is not the census year. Boundary data were processed in 2022; their 2026 metadata timestamp does not make the geometries newly surveyed. Government inputs are CC BY 4.0. No open license is asserted for Tripadvisor: this project stores only a small set of attributed factual metadata, not review prose or photographs.

A bounded follow-up audit on 11 October 2026 reconfirmed 2024 as the latest available census year through a direct API maximum-year query. The two official datasets' processing dates were unchanged. The API response is saved in `data/raw/source-audit-2026-10-11.json`; review spot checks and independently reconciled statistics are documented in `docs/source-audit.md`. The review dataset remains the 6 October snapshot.

## Material risks and repairs

- **High, confirmed: selection bias and small sample.** Avoid city-wide ranking claims, causal interpretations and statistical generalisation. The site should prominently say '31 selected listings'.
- **Medium, confirmed: periods differ.** Keep 2024 census context separate from review snapshots accessed in 2026; never imply they form a synchronized census.
- **Medium, confirmed: four unresolved locations.** Exclude them from the map and state its 27-listing denominator. Preserve them in the review sample.
- **Medium, confirmed: cuisine and dietary interpretation.** Use 'first listed cuisine' and 'lists ... options'; do not treat missing tags as no provision or guarantee allergy safety.
- **Low, checked: source-row duplication.** Indoor/outdoor records are aggregated explicitly, so venue counts are not inflated by seating type.
