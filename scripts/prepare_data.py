"""Prepare the saved, attributed coursework data; standard library only.

Run: python scripts/prepare_data.py
All inputs remain untouched. Re-running produces deterministic JSON and a QA note.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data/raw", ROOT / "data/processed"
CHECKED = "2026-10-06"
API = "https://data.melbourne.vic.gov.au/explore/dataset/"

# WGS84 transverse Mercator, UTM zone 55 south (EPSG:32755). Snyder's
# forward/inverse series, truncated at A^6 / D^6; intended only for Melbourne.
A = 6378137.0
F = 1 / 298.257223563
E2 = F * (2 - F)
EP2 = E2 / (1 - E2)
K0 = 0.9996
LON0 = math.radians(147)


def project(lon, lat):
    phi, lam = math.radians(lat), math.radians(lon)
    s, c, t = math.sin(phi), math.cos(phi), math.tan(phi)
    n = A / math.sqrt(1 - E2 * s * s)
    tt, cc, aa = t * t, EP2 * c * c, c * (lam - LON0)
    m = A * ((1 - E2 / 4 - 3 * E2**2 / 64 - 5 * E2**3 / 256) * phi
             - (3 * E2 / 8 + 3 * E2**2 / 32 + 45 * E2**3 / 1024) * math.sin(2 * phi)
             + (15 * E2**2 / 256 + 45 * E2**3 / 1024) * math.sin(4 * phi)
             - 35 * E2**3 / 3072 * math.sin(6 * phi))
    x = K0 * n * (aa + (1 - tt + cc) * aa**3 / 6
                 + (5 - 18 * tt + tt**2 + 72 * cc - 58 * EP2) * aa**5 / 120) + 500000
    y = K0 * (m + n * t * (aa**2 / 2 + (5 - tt + 9 * cc + 4 * cc**2) * aa**4 / 24
                           + (61 - 58 * tt + tt**2 + 600 * cc - 330 * EP2) * aa**6 / 720)) + 10000000
    return x, y


def unproject(x, y):
    x, y = x - 500000, y - 10000000
    mu = (y / K0) / (A * (1 - E2 / 4 - 3 * E2**2 / 64 - 5 * E2**3 / 256))
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    phi = (mu + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
           + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
           + 151 * e1**3 / 96 * math.sin(6 * mu) + 1097 * e1**4 / 512 * math.sin(8 * mu))
    s, c, t = math.sin(phi), math.cos(phi), math.tan(phi)
    n = A / math.sqrt(1 - E2 * s * s)
    r = A * (1 - E2) / (1 - E2 * s * s)**1.5
    tt, cc, d = t * t, EP2 * c * c, x / (n * K0)
    lat = phi - n * t / r * (d**2 / 2 - (5 + 3 * tt + 10 * cc - 4 * cc**2 - 9 * EP2) * d**4 / 24
                           + (61 + 90 * tt + 298 * cc + 45 * tt**2 - 252 * EP2 - 3 * cc**2) * d**6 / 720)
    lon = LON0 + (d - (1 + 2 * tt + cc) * d**3 / 6
                  + (5 - 2 * cc + 28 * tt - 3 * cc**2 + 8 * EP2 + 24 * tt**2) * d**5 / 120) / c
    return [math.degrees(lon), math.degrees(lat)]


def signed_area(ring):
    # Translate coordinates first to avoid cancellation of large UTM values.
    x0, y0 = ring[0]
    p = [(x - x0, y - y0) for x, y in ring]
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(p, p[1:])) / 2


def polygons(geometry):
    assert geometry["type"] in ("Polygon", "MultiPolygon")
    return [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]


def projected_area(geometry):
    return sum(sum((1 if i == 0 else -1) * abs(signed_area([project(*p) for p in ring]))
                   for i, ring in enumerate(poly)) for poly in polygons(geometry))


def d3_winding(geometry):
    """D3 spherical geometry expects clockwise exterior / anticlockwise holes."""
    geometry = deepcopy(geometry)
    for poly in polygons(geometry):
        for i, ring in enumerate(poly):
            if (signed_area(ring) > 0) == (i == 0):
                ring.reverse()
    return geometry


def load(name):
    return json.loads((RAW / name).read_text(encoding="utf-8"))


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# An explicit crosswalk prevents fuzzy-name matches to other branches.
# Tuple: property_id, exact CLUE trading name. Business addresses are verified
# in the human-readable audit. Withheld address conflicts remain unmapped.
CROSSWALK = {
    "Rice Paper Scissors": ("104651", "Rice Paper Scissors"),
    "Hochi Mama": ("105827", "Hochi Mama"),
    "Brick Lane Melbourne": ("104560", "Brick Lane Cafe"),
    "Straight Outta Saigon": ("101126", "Straight Outta Saigon"),
    "Da Guido La Pasta": ("106249", "Da Guido"),
    "Foglia di Fico": ("108958", "Foglia Di Fico"),
    "11 Inch Pizza": ("110669", "11 Inch Pizza"),
    "Waterfront": ("110606", "Waterfront (Southgate)"),
    "The Meat & Wine Co Southbank": ("575820", "The Meat & Wine Co"),
    "The Hardware Societe": ("103957", "The Hardware Societe"),
    "Roule Galette Melbourne": ("103940", "Roule Galette"),
    "Supernormal": ("102074", "Supernormal"),
    "Movida Bar de Tapas": ("104019", "Movida"),
    "Hofbrauhaus": ("106433", "Hofbrauhaus Restaurant"),
    "Tipo 00": ("105844", "Tipo 00"),
    "Chin Chin": ("103926", "Chin Chin Restaurant"),
    "Scopri": ("106956", "Scopri Italian Food & Wine"),
    "Da Guido 365": ("110670", "Da Guido 365"),
    "El Rincon": ("110688", "El Rincon"),
    "Stalactites Restaurant": ("108555", "Stalactites Restaurant"),
    "Shanghai Street": ("103187", "Shanghai Street"),
    "Hakata Gensuke Ramen": ("108585", "Hakata Gensuke"),
    "Vue De Monde": ("705127", "Vue de monde / The Lui Bar"),
    "Il Bacaro Cucina e Bar": ("105965", "Il Bacaro Cucina E Bar"),
    "Kazuki's": ("106086", "Kazuki's Restaurant"),
    "Coda": ("103930", "Coda Bar & Restaurant"),
    "Maha": ("108115", "Maha Restaurant"),
}
WITHHELD = {
    "The Railway Club Hotel Steakhouse": "unmatched_no_clue_match",
    "Grill Steak Seafood": "unmatched_address_difference",
    "Il Solito Posto": "unmatched_address_difference",
    "Flower Drum": "unmatched_address_difference",
}
# Read directly from these restaurants' existing source_url pages on CHECKED.
# Original raw file is retained; corrections are documented here and in QA.
ADDRESS_CORRECTIONS = {
    "The Hardware Societe": "10 Katherine Pl, Melbourne, Victoria 3000 Australia",
    "Movida Bar de Tapas": "1 Hosier Lane, Melbourne, Victoria 3000 Australia",
    "Da Guido 365": "365 Little Collins St, Melbourne, Victoria 3000 Australia",
}
JOIN_NOTES = {
    "11 Inch Pizza": "Same building and exact name; source shop 7A versus CLUE shop 6B. Building-level location only.",
    "Roule Galette Melbourne": "Same 241 Flinders Lane building; source shop 1 versus CLUE shop 1B.",
    "The Meat & Wine Co Southbank": "Source names Freshwater Place and 3 Queensbridge Street; CLUE names 3 Freshwater Place. Building-level location.",
    "Hofbrauhaus": "Source street range 18-26 includes selected CLUE Ground 18; CLUE also records 26-28. One source listing plotted once.",
    "Vue De Monde": "CLUE combines Vue de monde and The Lui Bar on level 55. Coordinate only; combined seat count is not assigned to the review listing.",
    "Grill Steak Seafood": "Source 68 Hardware Lane versus CLUE 66; possible address expansion. Coordinate withheld pending verification.",
    "Il Solito Posto": "Source 113 Collins Street versus CLUE 111; possible entrance difference. Coordinate withheld pending verification.",
    "Flower Drum": "Source 17 Market Lane versus CLUE 124-128 Bourke Street; possible entrance difference. Coordinate withheld pending verification.",
    "The Railway Club Hotel Steakhouse": "No matching establishment was found for 107 Raglan Street, Port Melbourne in the saved CLUE extract; no coordinate inferred.",
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, raw_reviews, geo = load("clue2024.json"), load("review_metadata.json"), load("small_areas.geojson")
    assert {str(r["census_year"]) for r in rows} == {"2024"}
    selected = [r for r in rows if str(r["industry_anzsic4_code"]) == "4511"]
    assert len(selected) == len({json.dumps(r, sort_keys=True) for r in selected}), "Duplicate raw rows"
    grouped = defaultdict(list)
    for row in selected:
        grouped[(row["property_id"], row["trading_name"].strip(), row["business_address"].strip())].append(row)
    venues = []
    for (pid, name, address), group in sorted(grouped.items()):
        assert len(group) == len({r["seating_type"] for r in group}), "Repeated seating type at one establishment"
        assert len({(r["longitude"], r["latitude"], r["clue_small_area"]) for r in group}) == 1
        first = group[0]
        lon, lat = first["longitude"], first["latitude"]
        assert 144 < lon < 146 and -39 < lat < -37
        assert all(r["number_of_seats"] >= 0 for r in group)
        venues.append({"id": sha256(f"{pid}|{name}|{address}".encode()).hexdigest()[:12],
                       "property_id": pid, "name": name, "address": address,
                       "area": first["clue_small_area"], "seats": sum(r["number_of_seats"] for r in group),
                       "longitude": lon, "latitude": lat, "census_year": 2024})
    area_counts = Counter(v["area"] for v in venues)
    area_features, area_errors = [], []
    for feature in geo["features"]:
        props, geometry = feature["properties"], feature["geometry"]
        area_m2 = projected_area(geometry)
        reference_m2 = float(props["shape_area"])
        area_errors.append(abs(area_m2 - reference_m2) / reference_m2)
        assert area_m2 > 0 and area_errors[-1] < 0.01, "Area differs >1% from official metadata"
        area = props["featurenam"]
        area_features.append({"type": "Feature", "properties": {
            "area": area, "venue_count": area_counts[area], "area_km2": round(area_m2 / 1e6, 6),
            "density": round(area_counts[area] / (area_m2 / 1e6), 3),
            "area_method": "WGS84 / UTM zone 55S projected polygon area"}, "geometry": d3_winding(geometry)})
    assert set(area_counts) <= {f["properties"]["area"] for f in area_features}
    assert sum(f["properties"]["venue_count"] for f in area_features) == len(venues)
    cells = Counter()
    roundtrip_error = 0
    for venue in venues:
        lon, lat = venue["longitude"], venue["latitude"]
        x, y = project(lon, lat)
        cells[(math.floor(x / 500), math.floor(y / 500))] += 1
        back = unproject(x, y)
        roundtrip_error = max(roundtrip_error, abs(back[0] - lon), abs(back[1] - lat))
    assert roundtrip_error < 1e-7
    grid_features = []
    for (i, j), count in sorted(cells.items()):
        x, y = i * 500, j * 500
        ring = [unproject(xx, yy) for xx, yy in [(x, y), (x, y + 500), (x + 500, y + 500), (x + 500, y), (x, y)]]
        grid_features.append({"type": "Feature", "properties": {"id": f"{i}_{j}", "count": count,
                              "cell_width_m": 500, "area_km2": 0.25, "easting": x, "northing": y},
                              "geometry": {"type": "Polygon", "coordinates": [ring]}})
    assert sum(f["properties"]["count"] for f in grid_features) == len(venues)

    reviews = []
    by_crosswalk = defaultdict(list)
    for venue in venues:
        by_crosswalk[(venue["property_id"], venue["name"])].append(venue)
    for raw in raw_reviews:
        name, rating = raw["name"], raw["rating"]
        assert 0 <= rating <= 5 and raw["review_count"] > 0
        match = None
        if name in CROSSWALK:
            candidates = by_crosswalk[CROSSWALK[name]]
            assert len(candidates) == 1, f"Ambiguous or missing crosswalk: {name}"
            match = candidates[0]
        else:
            assert name in WITHHELD, f"Unreviewed name: {name}"
        cuisines = [x.strip() for x in raw["cuisines"].split(",") if x.strip()]
        diets = [x.strip() for x in raw["diets"].split(",") if x.strip()]
        assert len(cuisines) == len(set(cuisines)) and len(diets) == len(set(diets)), "Repeated tags within a listing"
        reviews.append({"id": re.search(r"-d(\d+)-", raw["source_url"]).group(1), "name": name,
                        "rating": rating, "review_count": raw["review_count"], "price_raw": raw["price"],
                        "price": {"$": "Budget", "$$ - $$$": "Mid-range", "$$$$": "Premium"}[raw["price"]],
                        "cuisines": cuisines, "diets": diets, "primary_cuisine": cuisines[0] if cuisines else "Not listed",
                        "rating_band": "4.0–4.3" if rating <= 4.3 else "4.4–4.5" if rating <= 4.5 else "4.6–4.8",
                        "address": ADDRESS_CORRECTIONS.get(name, raw["address"]), "source_url": raw["source_url"],
                        "accessed_date": raw["accessed_date"], "verification": raw["verification"],
                        "longitude": match["longitude"] if match else None,
                        "latitude": match["latitude"] if match else None, "area": match["area"] if match else None,
                        "join_status": "matched_building" if match else WITHHELD[name],
                        "join_note": JOIN_NOTES.get(name, "Name/alias and street address agree with 2024 CLUE."),
                        "clue_venue_id": match["id"] if match else None,
                        "clue_address": match["address"] if match else None,
                        "vegetarian_listed": True if "Vegetarian friendly" in diets else None,
                        "vegan_listed": True if "Vegan options" in diets else None,
                        "gluten_free_listed": True if "Gluten free options" in diets else None})
    assert len({r["id"] for r in reviews}) == len(reviews) == len(raw_reviews)
    assert len({r["clue_venue_id"] for r in reviews if r["clue_venue_id"]}) == len(CROSSWALK)
    metadata = load("cafes-and-restaurants-with-seating-capacity-metadata.json")["metas"]["default"]
    geometa = load("small-areas-for-census-of-land-use-and-employment-clue-metadata.json")["metas"]["default"]
    diet_fields = ["vegetarian_listed", "vegan_listed", "gluten_free_listed"]
    diet_regions = Counter(tuple(r[f] is True for f in diet_fields) for r in reviews)
    assert sum(diet_regions.values()) == len(reviews)
    summary = {"accessed_date": CHECKED, "census_year": 2024, "raw_seating_rows": len(rows),
               "cafe_restaurant_seating_rows": len(selected), "venues": len(venues),
               "seats": sum(v["seats"] for v in venues), "small_areas": len(area_features),
               "populated_grid_cells": len(grid_features), "grid_size_m": 500,
               "review_sample": len(reviews), "mapped_reviews": len(CROSSWALK), "unmapped_reviews": len(WITHHELD),
               "rating_min": min(r["rating"] for r in reviews), "rating_max": max(r["rating"] for r in reviews),
               "rating_median": statistics.median(r["rating"] for r in reviews),
               "reviews_total": sum(r["review_count"] for r in reviews),
               "review_count_median": statistics.median(r["review_count"] for r in reviews),
               "price_counts": dict(Counter(r["price"] for r in reviews)),
               "diet_counts": dict(Counter(d for r in reviews for d in r["diets"])),
               "diet_overlap_regions": [dict(zip(diet_fields, combination), count=diet_regions[combination])
                                        for combination in [(False, False, False), (True, False, False),
                                                            (False, True, False), (False, False, True),
                                                            (True, True, False), (True, False, True),
                                                            (False, True, True), (True, True, True)]],
               "diet_overlap_note": "False in a region means the tag was not recorded, not that the option is unavailable.",
               "missing_diet_rows": sum(not r["diets"] for r in reviews),
               "first_listed_cuisine_counts": dict(Counter(r["primary_cuisine"] for r in reviews)),
               "all_cuisine_tag_counts": dict(sorted(Counter(c for r in reviews for c in r["cuisines"]).items(),
                                                    key=lambda item: (-item[1], item[0]))),
               "rating_distribution": [{"rating": rating, "count": count} for rating, count in
                                        sorted(Counter(r["rating"] for r in reviews).items())],
               "price_rating_medians": {price: statistics.median(r["rating"] for r in reviews if r["price"] == price)
                                        for price in ["Budget", "Mid-range", "Premium"]},
               "by_area": dict(area_counts), "projection_roundtrip_max_degrees": roundtrip_error,
               "max_polygon_area_relative_difference_from_official": max(area_errors),
               "sources": [
                   {"publisher": "City of Melbourne", "dataset": "Café, restaurant, bistro seats",
                    "url": API + "cafes-and-restaurants-with-seating-capacity/", "period": "2024",
                    "data_processed": metadata["data_processed"], "metadata_processed": metadata["metadata_processed"],
                    "license": "CC BY 4.0", "license_url": metadata["license_url"]},
                   {"publisher": "City of Melbourne", "dataset": "CLUE small areas",
                    "url": API + "small-areas-for-census-of-land-use-and-employment-clue/",
                    "data_processed": geometa["data_processed"], "metadata_processed": geometa["metadata_processed"],
                    "license": "CC BY 4.0", "license_url": geometa["license_url"]},
                   {"publisher": "Tripadvisor", "dataset": "31 selected Melbourne restaurant listings",
                    "url": "https://www.tripadvisor.com.au/Restaurants-g255100-Melbourne_Victoria.html",
                    "accessed_date": CHECKED, "freshness": "Web-reader snapshot; individual pages may be cached.",
                    "license": "No open-data license asserted; factual listing metadata only, with per-listing attribution."}],
               "limits": ["Non-random convenience sample: 25 featured listings plus six selected fine-dining listings.",
                          "Ratings are not representative of all Melbourne restaurants; sample range is 4.1–4.8.",
                          "Review counts are cumulative snapshots, not annual visits or a guarantee of rating reliability.",
                          "Price symbols are ordinal platform bands, not dollar amounts.",
                          "Primary cuisine means first source-listed tag; platform order is not a verified primary cuisine.",
                          "Dietary tags describe listing claims; absence means unknown, not unavailable.",
                          "2024 locations provide historical building-level context and are not current navigation guidance.",
                          "CLUE areas differ from gazetted suburbs; whole-polygon areas include non-dining land and water.",
                          "Four uncertain or unmatched locations are omitted from the review map but retained in all sample charts."]}
    audit_path = RAW / "source-audit-2026-10-11.json"
    if audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        year_query = next((q for q in audit["queries"] if q.get("success") and "select=" in q["url"]), None)
        if year_query:
            latest = year_query["payload"]["results"][0]["max(census_year)"]
            summary["official_freshness_audit"] = {"audit_date": audit["audit_date"],
                "latest_available_census_year": int(latest[:4]), "query_url": year_query["url"],
                "evidence_file": "data/raw/source-audit-2026-10-11.json"}
    write("venues.json", venues)
    write("reviews.json", reviews)
    write("areas.geojson", {"type": "FeatureCollection", "features": area_features})
    write("grids.geojson", {"type": "FeatureCollection", "features": grid_features})
    write("summary.json", summary)
    write_quality_note(summary, reviews)
    print(json.dumps({k: summary[k] for k in ["venues", "review_sample", "mapped_reviews", "unmapped_reviews", "populated_grid_cells", "projection_roundtrip_max_degrees", "max_polygon_area_relative_difference_from_official"]}, indent=2))


def write_quality_note(s, reviews):
    lines = ["# Data quality and reproducibility", "", f"Checked: {CHECKED}. Reproduce with `python scripts/prepare_data.py` from the project directory.", "",
             "## Grain and checks", "",
             f"The saved 2024 CLUE extract contains {s['raw_seating_rows']:,} rows across multiple industries. Filtering ANZSIC 4511 (Cafes and Restaurants) leaves {s['cafe_restaurant_seating_rows']:,} seating rows. Summing indoor and outdoor seats by property ID + trading name + business address yields **{s['venues']:,} establishment-location records** and {s['seats']:,} seats. Different property/address records are not merged just because they have the same trading name. This is an operational venue count, not a count of brands.", "",
             "No exact duplicate source rows, repeated seating types within an establishment, conflicting within-establishment coordinates/areas, missing venue coordinates, or invalid rating/review-count values were found. All area and grid counts reconcile to the venue total. Assertions in the preparation script stop processing if those conditions change.", "",
             "## Geography", "",
             "Polygon areas and 500 × 500 m cells use WGS84 / UTM zone 55 south (EPSG:32755), implemented using the standard transverse-Mercator series. Cells are aligned to multiples of 500 m in UTM eastings/northings. Only occupied cells are exported. Cells are not clipped to municipal boundaries: clipping would destroy the equal-area interpretation. Areas are projected surface areas, not ground-survey measurements.", "",
             f"Forward/inverse round-trip error across all venue coordinates is at most {s['projection_roundtrip_max_degrees']:.2e} degrees. Computed polygon area differs from the official `shape_area` by at most {100*s['max_polygon_area_relative_difference_from_official']:.6f}%. This independent metadata comparison checks the units and projection implementation. The source boundary coordinate reference is interpreted as WGS84 longitude/latitude as served in GeoJSON. Exterior rings are rewound clockwise for Vega/D3; holes counterclockwise.", "",
             "Small areas are CLUE statistical areas and do not exactly equal suburbs or postcodes. Density uses the full polygon area, including parks, industrial land and water. The source's area assignment is used for venue counts; no new boundary reassignment is inferred.", "",
             "## Review sample and freshness", "",
             "The 31 records are a convenience sample: 25 featured listings encountered on the Melbourne restaurant page plus six selected fine-dining listings. Selection was not random, exhaustive, or a reproducible city-wide rank sample. The sample contains only ratings from 4.1 to 4.8 and cannot estimate average Melbourne restaurant quality or establish a price/cuisine effect. Treat small cells and comparisons as descriptions of these listings only.", "",
             "Each record retains its source URL and access date. Web-reader pages may be cached: 6 October 2026 is an access date, not proof that all figures were refreshed that day. Review counts accumulate over each listing's lifetime. No annual time series, review text, sentiment, confidence intervals, actual meal prices or independent dietary verification are available.", "",
             "Price labels map `$` to Budget, `$$ - $$$` to Mid-range, and `$$$$` to Premium. These are ordinal bands. `primary_cuisine` is only the first listed cuisine tag, retained deterministically for grouping; labels such as Asian and International are broad platform tags, not a verified hierarchy. Cuisine and diet arrays retain all listed tags. Absent dietary flags are null (unknown), never false.", "",
             "The dietary overlap chart describes recorded labels. Of 31 listings, 23 record all three labels, two record vegetarian + vegan only, three record vegetarian + gluten-free only, one records vegetarian only, one records gluten-free only, and one has none recorded. Vegan-only and vegan + gluten-free without vegetarian both contain zero listings. Thus every vegan-tagged listing in this sample is also vegetarian-tagged. These set relationships describe the saved listing labels, not independently verified menus. In `summary.json`'s derived overlap regions, false means a tag was not recorded.", "",
             "The raw file had three missing addresses. The existing Tripadvisor source URLs were reread on 6 October 2026: Hardware Societe lists 10 Katherine Pl; Movida lists 1 Hosier Lane; Da Guido 365 lists 365 Little Collins St. Corrections are explicit in the script; the raw file remains untouched. One restaurant, Hakata Gensuke, has no saved dietary tags.", "",
             "## Joining locations", "",
             f"**{s['mapped_reviews']} of {s['review_sample']}** listings have an explicit name/address crosswalk to 2024 CLUE. Coordinates are building-level historical locations. Four listings remain unmapped; all 31 remain in non-spatial sample charts. A matched coordinate does not establish that the business is still open in 2026. The source review address and matched CLUE address are both retained. Review ratings are never copied to all venues in an area.", "",
             "| Listing | Status | Review address | CLUE address | Join note |", "|---|---|---|---|---|"]
    for r in reviews:
        lines.append("| " + " | ".join(str(x or "—").replace("|", "/") for x in [r["name"], r["join_status"], r["address"], r["clue_address"], r["join_note"]]) + " |")
    lines += ["", "Hofbrauhaus has two CLUE property records within the source street range; one building is selected and one review listing is plotted once. Vue de monde shares a CLUE record with The Lui Bar; no seat-count comparison is made at review-listing grain. Grill Steak Seafood, Il Solito Posto and Flower Drum have unresolved civic-address differences and are conservatively withheld from the map. The Railway Club Hotel's Raglan Street address is not matched in this municipal dataset.", "",
              "## Source timing and reuse", ""]
    for source in s["sources"]:
        lines += [f"- [{source['dataset']}]({source['url']}) — {source['publisher']}. " + (f"Data processed {source['data_processed']}; metadata processed {source['metadata_processed']}. " if "data_processed" in source else source["freshness"] + " ") + source["license"]]
    lines += ["", "The 2024 census is the newest year present in the downloaded official dataset checked for this project. The 2026 processing timestamp is not the census year. Boundary data were processed in 2022; their 2026 metadata timestamp does not make the geometries newly surveyed. Government inputs are CC BY 4.0. No open license is asserted for Tripadvisor: this project stores only a small set of attributed factual metadata, not review prose or photographs.", "",
              "A bounded follow-up audit on 11 October 2026 reconfirmed 2024 as the latest available census year through a direct API maximum-year query. The two official datasets' processing dates were unchanged. The API response is saved in `data/raw/source-audit-2026-10-11.json`; review spot checks and independently reconciled statistics are documented in `docs/source-audit.md`. The review dataset remains the 6 October snapshot.", "",
              "## Material risks and repairs", "",
              "- **High, confirmed: selection bias and small sample.** Avoid city-wide ranking claims, causal interpretations and statistical generalisation. The site should prominently say '31 selected listings'.",
              "- **Medium, confirmed: periods differ.** Keep 2024 census context separate from review snapshots accessed in 2026; never imply they form a synchronized census.",
              "- **Medium, confirmed: four unresolved locations.** Exclude them from the map and state its 27-listing denominator. Preserve them in the review sample.",
              "- **Medium, confirmed: cuisine and dietary interpretation.** Use 'first listed cuisine' and 'lists ... options'; do not treat missing tags as no provision or guarantee allergy safety.",
              "- **Low, checked: source-row duplication.** Indoor/outdoor records are aggregated explicitly, so venue counts are not inflated by seating type.", ""]
    path = ROOT / "docs/data-quality.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
