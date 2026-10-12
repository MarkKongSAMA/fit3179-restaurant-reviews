"""Export the four website datasets as Excel-readable CSV downloads.

Run from any directory: python path/to/scripts/export_downloads.py

CSV files use UTF-8 with a BOM and CRLF line endings. Arrays become semicolon-
separated text, missing values become empty cells, and booleans become true/false.
Text that could be interpreted as a spreadsheet formula is prefixed with one
apostrophe. This intentional escaping can be visible in some spreadsheet apps;
the original JSON remains the authoritative, unescaped data. Numeric values,
including negative latitudes, are never escaped or rounded.

The area/grid CSVs are tabular reading copies. Their geometry_geojson column
retains the complete WGS84 geometry as compact JSON; the website maps continue
to load the separate, unchanged data/processed/*.geojson files.

Only Python's standard library is needed. Source JSON/GeoJSON is never modified.
"""
from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed"
OUTPUT = ROOT / "data" / "downloads"
CLUE_URL = "https://data.melbourne.vic.gov.au/explore/dataset/cafes-and-restaurants-with-seating-capacity/"
AREAS_URL = "https://data.melbourne.vic.gov.au/explore/dataset/small-areas-for-census-of-land-use-and-employment-clue/"
TARGETS = (
    ("reviews", "reviews.json", 31),
    ("venues", "venues.json", 1645),
    ("areas", "areas.geojson", 13),
    ("grids", "grids.geojson", 87),
)
FORMULA_PREFIXES = "=+-@＝＋－＠"
LEADING_SPACE = " \t\r\n\v\f\ufeff"


def formula_like(text: str) -> bool:
    """Catch leading formula operators, including after hidden whitespace."""
    stripped = text.lstrip(LEADING_SPACE)
    return bool(stripped and stripped[0] in FORMULA_PREFIXES) or text.startswith(("\t", "\r", "\n"))


def cell(value: Any) -> tuple[str, bool]:
    """Return serialized cell text and whether formula escaping was required."""
    if value is None:
        return "", False
    if isinstance(value, bool):
        return str(value).lower(), False
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            raise ValueError(f"Non-finite numeric value: {value!r}")
        return str(value), False
    if isinstance(value, list):
        if any(not isinstance(item, str) or ";" in item for item in value):
            raise ValueError("Array values must be strings without semicolons for a lossless CSV join")
        text = "; ".join(value)
    elif isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    elif isinstance(value, str):
        text = value
    else:
        raise TypeError(f"Unsupported cell type: {type(value).__name__}")
    escaped = formula_like(text)
    return ("'" + text if escaped else text), escaped


def read_rows(kind: str, filename: str) -> list[dict[str, Any]]:
    source = json.loads((INPUT / filename).read_text(encoding="utf-8"))
    if kind in ("reviews", "venues"):
        if not isinstance(source, list) or any(not isinstance(row, dict) for row in source):
            raise ValueError(f"Expected an array of records in {filename}")
        rows = [dict(row) for row in source]
        for row in rows:
            # Review source_url already attributes ratings; keep it untouched.
            column = "location_source_url" if kind == "reviews" else "source_url"
            if column in row:
                raise ValueError(f"Unexpected existing provenance column: {column}")
            row[column] = CLUE_URL
        return rows
    if source.get("type") != "FeatureCollection":
        raise ValueError(f"Expected a FeatureCollection in {filename}")
    rows = []
    for feature in source["features"]:
        row = dict(feature["properties"])
        geometry = feature["geometry"]
        extra = {
            "geometry_type": geometry["type"],
            "geometry_geojson": geometry,
            "geometry_crs": "EPSG:4326 (WGS84 longitude, latitude)",
            "source_url": CLUE_URL,
            "original_geojson_path": f"data/processed/{filename}",
        }
        if kind == "areas":
            extra["geometry_source_url"] = AREAS_URL
        else:
            extra["geometry_method"] = "500 m square cells in WGS84 / UTM zone 55S, exported as WGS84 longitude/latitude"
        if set(row) & set(extra):
            raise ValueError("A derived export field would overwrite an existing GeoJSON property")
        row.update(extra)
        rows.append(row)
    return rows


def make_csv(rows: list[dict[str, Any]]) -> tuple[bytes, list[str], int]:
    # Preserve source field order and include fields first appearing in later rows.
    fields = list(dict.fromkeys(key for row in rows for key in row))
    encoded_rows = []
    escaped_count = 0
    for row in rows:
        encoded = {}
        for field in fields:
            encoded[field], escaped = cell(row.get(field))
            escaped_count += int(escaped)
        encoded_rows.append(encoded)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, dialect="excel", lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(encoded_rows)
    return buffer.getvalue().encode("utf-8-sig"), fields, escaped_count


def validate(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    """Reopen the actual CSV and compare every value with the source projection."""
    if not path.read_bytes().startswith(b"\xef\xbb\xbf"):
        raise AssertionError(f"Missing UTF-8 BOM: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual = list(reader)
        if reader.fieldnames != fields or len(actual) != len(rows):
            raise AssertionError(f"Header/record-count mismatch: {path}")
    for index, (original, exported) in enumerate(zip(rows, actual), 1):
        for field in fields:
            source = original.get(field)
            value = exported[field]
            # Decode independently by the original type. CSV carries text only.
            if isinstance(source, bool):
                equal = value == ("true" if source else "false")
            elif source is None:
                equal = value == ""
            elif isinstance(source, (int, float)):
                equal = (int(value) if isinstance(source, int) else float(value)) == source
            else:
                source_text = "; ".join(source) if isinstance(source, list) else source
                if isinstance(source_text, str) and formula_like(source_text):
                    if not value.startswith("'"):
                        raise AssertionError(f"Missing formula protection: {path.name}, record {index}, field {field}")
                    value = value[1:]
                if isinstance(source, list):
                    equal = ([] if not value else value.split("; ")) == source
                elif isinstance(source, dict):
                    equal = json.loads(value) == source
                else:
                    equal = value == source
            if not equal:
                raise AssertionError(f"Value mismatch in {path.name}, record {index}, field {field}")


def main() -> None:
    prepared = []
    for kind, filename, expected_count in TARGETS:
        rows = read_rows(kind, filename)
        if len(rows) != expected_count:
            raise ValueError(f"Expected {expected_count} records in {filename}, found {len(rows)}; review the dataset before exporting")
        payload, fields, escaped_count = make_csv(rows)
        prepared.append((kind, rows, payload, fields, escaped_count))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for kind, rows, payload, fields, escaped_count in prepared:
        path = OUTPUT / f"{kind}.csv"
        path.write_bytes(payload)
        validate(path, rows, fields)
        print(f"{path.relative_to(ROOT)}: {len(rows)} records, {len(fields)} columns, "
              f"{len(payload):,} bytes, {escaped_count} text cells escaped; verified")
    print("CSV copies are for spreadsheet reading. Original JSON/GeoJSON files remain unchanged and power the maps.")
    print("Formula-like text is prefixed with an apostrophe; original values remain in the source JSON/GeoJSON.")


if __name__ == "__main__":
    main()
