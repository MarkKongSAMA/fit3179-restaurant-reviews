"""Build the twelve original, source-backed Vega / Vega-Lite chart specifications.

Run from any working directory with Python 3. No third-party dependency is needed.
All data URLs are relative to the website root, not the specs directory. The host
page injects filtered rows into the named `reviews` dataset in charts 02, 05, 12.
"""
from pathlib import Path
import copy
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "specs"
OUT.mkdir(exist_ok=True)

GREEN = "#28746b"
INK = "#183b35"
PRICES = ["Budget", "Mid-range", "Premium"]
COLORS = ["#d5a245", GREEN, "#a65a3c"]
PRICE_SCALE = {"domain": PRICES, "range": COLORS}
REVIEW_URL = "data/processed/reviews.json"
AREAS = {"url": "data/processed/areas.geojson", "format": {"type": "json", "property": "features"}}
PROJECTION = {"type": "conicEqualArea", "parallels": [-36, -38], "rotate": [-145, 0, 0]}
PRICE_COLOR = {"field": "price", "type": "nominal", "scale": PRICE_SCALE,
               "legend": {"title": "Price tier", "orient": "bottom", "direction": "horizontal"}}
RATING_SCALE = {"domain": [4, 5], "zero": False, "nice": False}
SOURCE_TOOLTIP = [
    {"field": "name", "type": "nominal", "title": "Restaurant"},
    {"field": "rating", "type": "quantitative", "title": "Rating / 5", "format": ".1f"},
    {"field": "review_count", "type": "quantitative", "title": "Cumulative reviews", "format": ",.0f"},
    {"field": "price", "type": "nominal", "title": "Price tier"},
    {"field": "source_url", "type": "nominal", "title": "Listing source"},
]


def vl(description, height=260, **content):
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": description,
        "width": "container",
        "height": height,
        "autosize": {"type": "fit", "contains": "padding", "resize": True},
        "background": "transparent",
        "config": {
            "font": "Arial",
            "view": {"stroke": None},
            "axis": {"labelFontSize": 12, "titleFontSize": 12, "titleFontWeight": "normal",
                     "labelColor": INK, "titleColor": INK, "domainColor": "#bdc9c2",
                     "tickColor": "#bdc9c2", "gridColor": "#e6ebe5", "labelPadding": 6, "titlePadding": 10},
            "legend": {"labelFontSize": 12, "titleFontSize": 12, "titleColor": INK,
                       "labelColor": INK, "symbolStrokeWidth": 1, "padding": 4},
            "title": {"fontSize": 13, "color": INK, "anchor": "start", "fontWeight": "normal"},
        },
        **content,
    }


def write(name, spec):
    if name[:2] in {"01", "02", "03"}:
        # Label anchors are computed from the supplied official area geometry.
        label_layer = {
            "data": copy.deepcopy(AREAS),
            "transform": [
                {"filter": {"field": "properties.area", "oneOf": ["Melbourne (CBD)", "Carlton", "Docklands"]}},
                {"calculate": "geoCentroid(null, datum)", "as": "label_centroid"},
                {"calculate": "datum.label_centroid[0]", "as": "label_lon"},
                {"calculate": "datum.label_centroid[1]", "as": "label_lat"},
                {"calculate": "datum.properties.area === 'Melbourne (CBD)' ? 'CBD' : datum.properties.area", "as": "label"},
            ],
            "mark": {"type": "text", "fontSize": 11, "fontWeight": "bold", "fill": INK},
            "encoding": {"longitude": {"field": "label_lon", "type": "quantitative"},
                         "latitude": {"field": "label_lat", "type": "quantitative"},
                         "text": {"field": "label"}},
        }
        halo = copy.deepcopy(label_layer)
        halo["mark"].update({"fill": "#fffdf7", "stroke": "#fffdf7", "strokeWidth": 3, "strokeOpacity": 0.85})
        if "layer" not in spec:
            spec["layer"] = [{key: spec.pop(key) for key in ["data", "transform", "mark", "encoding"] if key in spec}]
        if name.startswith("02"):
            spec["layer"][1:1] = [halo, label_layer]
        else:
            spec["layer"].extend([halo, label_layer])
    (OUT / name).write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


base_map = {"data": AREAS, "mark": {"type": "geoshape", "fill": "#edf0e8", "stroke": "#ffffff", "strokeWidth": 0.8}}

write("01-venue-density.vl.json", vl(
    "Choropleth: 2024 CLUE cafe/restaurant establishment counts divided by whole small-area square kilometres. Conic equal-area projection centred by rotation on Melbourne. Historical municipal context; not filtered by the review controls.",
    330, data=AREAS, projection=PROJECTION,
    transform=[{"calculate": "datum.properties.density < 10 ? '< 10' : datum.properties.density < 30 ? '10–<30' : datum.properties.density < 100 ? '30–<100' : datum.properties.density < 300 ? '100–<300' : '≥ 300'", "as": "density_class"}],
    mark={"type": "geoshape", "stroke": "#ffffff", "strokeWidth": 0.9},
    encoding={
        "color": {"field": "density_class", "type": "ordinal", "title": "Venues / km²",
                  "scale": {"domain": ["< 10", "10–<30", "30–<100", "100–<300", "≥ 300"],
                            "range": ["#f1f3df", "#cddfc0", "#92bda4", "#4d927e", "#195c48"]},
                  "legend": {"type": "symbol", "orient": "bottom", "direction": "horizontal", "columns": 2,
                             "symbolType": "square", "symbolSize": 100, "columnPadding": 18, "rowPadding": 4,
                             "title": "Venues / km²"}},
        "tooltip": [
            {"field": "properties.area", "type": "nominal", "title": "CLUE area"},
            {"field": "properties.venue_count", "type": "quantitative", "title": "2024 establishments", "format": ",.0f"},
            {"field": "properties.area_km2", "type": "quantitative", "title": "Whole area (km²)", "format": ".2f"},
            {"field": "properties.density", "type": "quantitative", "title": "Venues / km²", "format": ".1f"},
        ],
    },
))

write("02-review-footprint.vl.json", vl(
    "Proportional-symbol map. The host injects filtered restaurant rows into the named reviews dataset. Only valid matched coordinates are drawn. Circle AREA, not radius, is proportional to cumulative review count. Background boundaries keep the map extent fixed during filtering.",
    330, data={"name": "reviews", "values": []}, projection=PROJECTION,
    layer=[base_map, {
        "transform": [{"filter": "isValid(datum.longitude) && isValid(datum.latitude)"}],
        "mark": {"type": "circle", "stroke": "#ffffff", "strokeWidth": 0.8, "opacity": 0.77},
        "encoding": {
            "longitude": {"field": "longitude", "type": "quantitative"},
            "latitude": {"field": "latitude", "type": "quantitative"},
            "size": {"field": "review_count", "type": "quantitative", "title": "Reviews",
                     "scale": {"type": "linear", "domain": [0, 6500], "range": [0, 750]},
                     "legend": {"orient": "bottom", "values": [500, 2000, 6000], "format": ",.0f"}},
            "color": {"field": "rating", "type": "quantitative", "title": "Rating / 5",
                      "scale": {"domain": [4, 5], "range": ["#e4c99a", "#195c48"]},
                      "legend": {"orient": "bottom", "gradientLength": 100, "format": ".1f"}},
            "order": {"field": "review_count", "type": "quantitative", "sort": "descending"},
            "tooltip": SOURCE_TOOLTIP + [
                {"field": "area", "type": "nominal", "title": "2024 CLUE area"},
                {"field": "join_note", "type": "nominal", "title": "Location match"},
            ],
        },
    }],
))

write("03-dining-clusters.vl.json", vl(
    "Bin map: 2024 CLUE establishment locations counted in full 500 m by 500 m UTM zone 55S squares. Each cell is 0.25 km² before display projection. Only occupied cells are supplied. Cells remain full squares at the municipal boundary. Not filtered by review controls.",
    330, projection=PROJECTION,
    layer=[base_map, {
        "data": {"url": "data/processed/grids.geojson", "format": {"type": "json", "property": "features"}},
        "transform": [{"calculate": "datum.properties.count < 5 ? '1–4' : datum.properties.count < 15 ? '5–14' : datum.properties.count < 40 ? '15–39' : datum.properties.count < 80 ? '40–79' : '80+'", "as": "count_class"}],
        "mark": {"type": "geoshape", "stroke": "#fffdf7", "strokeWidth": 0.35},
        "encoding": {
            "color": {"field": "count_class", "type": "ordinal", "title": "Venues / cell",
                      "scale": {"domain": ["1–4", "5–14", "15–39", "40–79", "80+"],
                                "range": ["#f6e6c7", "#e7bc82", "#d39356", "#b36636", "#814221"]},
                      "legend": {"type": "symbol", "orient": "bottom", "direction": "horizontal", "columns": 2,
                                 "symbolType": "square", "symbolSize": 100, "columnPadding": 18, "rowPadding": 4}},
            "tooltip": [
                {"field": "properties.count", "type": "quantitative", "title": "2024 establishments", "format": ",.0f"},
                {"field": "properties.cell_width_m", "type": "quantitative", "title": "Cell side (m)", "format": ".0f"},
                {"field": "properties.area_km2", "type": "quantitative", "title": "Cell area (km²)", "format": ".2f"},
            ],
        },
    }],
))

write("04-rating-histogram.vl.json", vl(
    "Histogram of the complete 31-listing convenience sample. Ratings are recorded to 0.1; equal-width bins are centred on those reported values. Missing score bins have zero observations. The rating axis is deliberately zoomed to 4–5.",
    data={"url": REVIEW_URL},
    transform=[
        {"calculate": "round(datum.rating * 10) / 10 - 0.05", "as": "bin_start"},
        {"calculate": "round(datum.rating * 10) / 10 + 0.05", "as": "bin_end"},
        {"aggregate": [{"op": "count", "as": "restaurants"}], "groupby": ["rating", "bin_start", "bin_end"]},
    ],
    mark={"type": "bar", "color": GREEN, "binSpacing": 1},
    encoding={
        "x": {"field": "bin_start", "type": "quantitative", "bin": "binned", "title": "Rating / 5 (zoomed)",
              "scale": RATING_SCALE, "axis": {"values": [4, 4.2, 4.4, 4.6, 4.8, 5], "format": ".1f", "grid": False}},
        "x2": {"field": "bin_end"},
        "y": {"field": "restaurants", "type": "quantitative", "title": "Restaurants", "axis": {"tickMinStep": 1}, "scale": {"zero": True}},
        "tooltip": [{"field": "rating", "type": "quantitative", "title": "Reported rating", "format": ".1f"},
                    {"field": "restaurants", "type": "quantitative", "title": "Sample restaurants", "format": ".0f"}],
    },
))

write("05-rating-attention.vl.json", vl(
    "Rating versus cumulative review count for injected sample rows. The logarithmic review axis is fixed while filtering. Drag an interval brush; the host reads the brush signal and filters the map and shortlist, while this view retains the other points for context. Double-click clears the brush.",
    data={"name": "reviews", "values": []},
    params=[{"name": "brush", "select": {"type": "interval", "encodings": ["x", "y"], "clear": "dblclick", "zoom": False,
                                           "mark": {"fill": "#c5dcd2", "fillOpacity": 0.35, "stroke": GREEN}}}],
    mark={"type": "point", "filled": True, "size": 76, "stroke": "#ffffff", "strokeWidth": 0.7},
    encoding={
        "x": {"field": "review_count", "type": "quantitative", "title": "Cumulative reviews (log scale)",
              "scale": {"type": "log", "domain": [200, 7000], "nice": False},
              "axis": {"values": [200, 500, 1000, 2000, 6000], "format": "~s"}},
        "y": {"field": "rating", "type": "quantitative", "title": "Rating / 5 (zoomed)", "scale": RATING_SCALE,
              "axis": {"values": [4, 4.2, 4.4, 4.6, 4.8, 5], "format": ".1f"}},
        "color": PRICE_COLOR,
        "opacity": {"condition": {"param": "brush", "value": 0.95}, "value": 0.18},
        "tooltip": SOURCE_TOOLTIP,
    },
))

write("06-price-boxplot.vl.json", vl(
    "Rating distributions by ordinal price tier for all 31 listings. Boxes show quartiles and median, whiskers show minimum and maximum, and every listing is also drawn as a point. Horizontal offsets only separate marks and carry no meaning. Group sizes are displayed. Rating axis zoomed to 4–5.",
    data={"url": REVIEW_URL},
    encoding={
        "x": {"field": "price", "type": "nominal", "sort": PRICES, "title": None, "axis": {"labelAngle": 0}},
    },
    layer=[
        {"mark": {"type": "boxplot", "extent": "min-max", "size": 38,
                  "box": {"fillOpacity": 0.2, "stroke": INK}, "median": {"color": INK}, "ticks": {"size": 18, "color": INK},
                  "rule": {"color": INK}},
         "encoding": {"color": {**PRICE_COLOR, "legend": None},
                      "y": {"field": "rating", "type": "quantitative", "title": "Rating / 5 (zoomed)", "scale": RATING_SCALE,
                            "axis": {"values": [4, 4.2, 4.4, 4.6, 4.8, 5], "format": ".1f"}}}},
        {"transform": [{"calculate": "(toNumber(datum.id) % 11) - 5", "as": "display_offset"}],
         "mark": {"type": "point", "filled": True, "size": 39, "stroke": "#ffffff", "strokeWidth": 0.5, "opacity": 0.9,
                  "xOffset": {"expr": "datum.display_offset * 3.4"}},
         "encoding": {"y": {"field": "rating", "type": "quantitative", "scale": RATING_SCALE},
                      "color": {**PRICE_COLOR, "legend": None}, "tooltip": SOURCE_TOOLTIP}},
        {"transform": [{"aggregate": [{"op": "count", "as": "n"}], "groupby": ["price"]},
                       {"calculate": "'n = ' + datum.n", "as": "sample_label"}],
         "mark": {"type": "text", "fontSize": 12, "color": INK, "baseline": "top"},
         "encoding": {"y": {"value": 5}, "text": {"field": "sample_label"}}},
    ],
))

write("07-cuisine-price.vl.json", vl(
    "The 12 most frequent source-listed cuisine tags, selected by total listing frequency descending then tag name ascending. Each restaurant may have several tags. Cell counts are restaurants carrying that tag in a price tier; absent combinations are explicit zero cells. This is not an exclusive cuisine classification.",
    330, data={"url": REVIEW_URL},
    transform=[
        {"flatten": ["cuisines"], "as": ["cuisine"]},
        {"joinaggregate": [{"op": "count", "as": "tag_total"}], "groupby": ["cuisine"]},
        {"window": [{"op": "dense_rank", "as": "tag_rank"}], "sort": [{"field": "tag_total", "order": "descending"}, {"field": "cuisine", "order": "ascending"}]},
        {"filter": "datum.tag_rank <= 12"},
        {"aggregate": [{"op": "count", "as": "restaurants"}], "groupby": ["cuisine", "price", "tag_total", "tag_rank"]},
        {"impute": "restaurants", "key": "price", "keyvals": PRICES, "groupby": ["cuisine", "tag_total", "tag_rank"], "value": 0},
    ],
    encoding={
        "x": {"field": "price", "type": "nominal", "sort": PRICES, "title": None, "axis": {"labelAngle": 0}},
        "y": {"field": "cuisine", "type": "nominal", "title": None, "sort": {"field": "tag_rank", "order": "ascending"}, "axis": {"labelLimit": 115}},
        "tooltip": [{"field": "cuisine", "type": "nominal", "title": "Listed tag"},
                    {"field": "price", "type": "nominal", "title": "Price tier"},
                    {"field": "restaurants", "type": "quantitative", "title": "Restaurants", "format": ".0f"},
                    {"field": "tag_total", "type": "quantitative", "title": "Tag total, all prices", "format": ".0f"}],
    },
    layer=[
        {"mark": {"type": "rect", "stroke": "#fffdf7", "strokeWidth": 2},
         "encoding": {"color": {"field": "restaurants", "type": "quantitative", "scale": {"domain": [0, 8], "range": ["#f1f3e8", "#195c48"]},
                                "legend": None}}},
        {"mark": {"type": "text", "fontSize": 12}, "encoding": {"text": {"field": "restaurants", "type": "quantitative", "format": ".0f"},
            "color": {"condition": {"test": "datum.restaurants >= 5", "value": "#ffffff"}, "value": INK}}},
    ],
))

write("08-dietary-options.vl.json", vl(
    "Marginal counts of source-listed dietary tags in the full sample. A restaurant may contribute to several bars. Missing tags are unknown and are not evidence that a dietary option is unavailable. Counts describe listing claims, not independently checked menus.",
    200, data={"url": REVIEW_URL},
    transform=[{"flatten": ["diets"], "as": ["diet"]},
               {"filter": {"field": "diet", "oneOf": ["Vegetarian friendly", "Vegan options", "Gluten free options"]}},
               {"aggregate": [{"op": "count", "as": "restaurants"}], "groupby": ["diet"]}],
    encoding={
        "y": {"field": "diet", "type": "nominal", "title": None, "sort": ["Vegetarian friendly", "Gluten free options", "Vegan options"], "axis": {"labelLimit": 140}},
        "x": {"field": "restaurants", "type": "quantitative", "title": "Restaurants with tag (of 31)", "scale": {"domain": [0, 33]}, "axis": {"values": [0, 10, 20, 30]}},
        "tooltip": [{"field": "diet", "type": "nominal", "title": "Listing tag"},
                    {"field": "restaurants", "type": "quantitative", "title": "Sample restaurants", "format": ".0f"}],
    },
    layer=[{"mark": {"type": "bar", "color": GREEN, "size": 24}},
           {"mark": {"type": "text", "align": "left", "dx": 5, "fontSize": 12, "color": INK},
            "encoding": {"text": {"field": "restaurants", "type": "quantitative", "format": ".0f"}}}],
))

write("09-budget-grid.vl.json", vl(
    "Unit grid of the complete convenience sample: exactly one whole square for each of 31 restaurants. Squares are ordered by ordinal price tier and name. Price categories are platform symbols, not dollar amounts. Hover a square to identify the listing.",
    190, data={"url": REVIEW_URL},
    transform=[
        {"calculate": "indexof(['Budget', 'Mid-range', 'Premium'], datum.price)", "as": "price_order"},
        {"window": [{"op": "row_number", "as": "cell"}], "sort": [{"field": "price_order"}, {"field": "name"}]},
        {"calculate": "(datum.cell - 1) % 8", "as": "column"},
        {"calculate": "floor((datum.cell - 1) / 8)", "as": "row"},
    ],
    mark={"type": "point", "shape": "square", "filled": True, "size": 675, "opacity": 1, "stroke": "#fffdf7", "strokeWidth": 1},
    encoding={
        "x": {"field": "column", "type": "ordinal", "scale": {"domain": list(range(8))}, "axis": None},
        "y": {"field": "row", "type": "ordinal", "scale": {"domain": list(range(4))}, "axis": None},
        "color": PRICE_COLOR,
        "tooltip": SOURCE_TOOLTIP,
    },
))

native = {
    "$schema": "https://vega.github.io/schema/vega/v5.json",
    "width": 330, "height": 300, "padding": 0, "autosize": "none", "background": "transparent",
    "config": {"font": "Arial", "text": {"font": "Arial", "fontSize": 12, "fill": INK}},
}

tree = copy.deepcopy(native)
tree.update({
    "description": "Nested treemap of cumulative review counts in the 31-listing sample. Hierarchy is sample > price tier > restaurant. Rectangle area shows review volume, not rating or market share. Price groups and leaf values are derived from reviews.json at runtime.",
    "data": [
        {"name": "raw", "url": REVIEW_URL, "format": {"type": "json"}},
        {"name": "total", "source": "raw", "transform": [{"type": "aggregate", "fields": ["review_count"], "ops": ["sum"], "as": ["reviews"]}]},
        {"name": "tree", "source": "raw", "transform": [
            {"type": "nest", "keys": ["price"], "generate": True},
            {"type": "treemap", "field": "review_count", "sort": {"field": "value", "order": "descending"},
             "method": "squarify", "ratio": 1.3, "round": True, "paddingInner": 2, "paddingOuter": 2, "paddingTop": 20,
             "size": [{"signal": "width"}, {"signal": "height"}]},
        ]},
        {"name": "groups", "source": "tree", "transform": [{"type": "filter", "expr": "datum.depth === 1"}]},
        {"name": "leaves", "source": "tree", "transform": [{"type": "filter", "expr": "datum.depth === 2"}]},
    ],
    "scales": [{"name": "priceColor", "type": "ordinal", **PRICE_SCALE}],
    "marks": [
        {"type": "rect", "from": {"data": "groups"}, "encode": {"update": {
            "x": {"field": "x0"}, "y": {"field": "y0"}, "x2": {"field": "x1"}, "y2": {"field": "y1"},
            "fill": {"value": "#e6ece3"}, "stroke": {"value": "#becbc0"}, "strokeWidth": {"value": 0.8},
            "tooltip": {"signal": "{'Price tier': datum.key, 'Cumulative reviews': format(datum.value, ',.0f')}"},
        }}},
        {"type": "text", "from": {"data": "groups"}, "encode": {"update": {
            "x": {"signal": "datum.x0 + 5"}, "y": {"signal": "datum.y0 + 4"}, "baseline": {"value": "top"},
            "text": {"field": "key"}, "fontWeight": {"value": "bold"}, "fontSize": {"value": 12},
            "limit": {"signal": "max(0, datum.x1 - datum.x0 - 10)"},
        }}},
        {"type": "rect", "name": "restaurantTiles", "from": {"data": "leaves"}, "encode": {
            "update": {"x": {"field": "x0"}, "y": {"field": "y0"}, "x2": {"field": "x1"}, "y2": {"field": "y1"},
                       "fill": {"scale": "priceColor", "field": "price"}, "stroke": {"value": "#fffdf7"}, "strokeWidth": {"value": 0.7},
                       "tooltip": {"signal": "{'Restaurant': datum.name, 'Price tier': datum.price, 'Reviews': format(datum.review_count, ',.0f'), 'Share of sample review total': format(datum.review_count / data('total')[0].reviews, '.1%'), 'Rating / 5': format(datum.rating, '.1f'), 'Source': datum.source_url}"}},
            "hover": {"stroke": {"value": INK}, "strokeWidth": {"value": 2}},
        }},
        {"type": "text", "interactive": False, "from": {"data": "leaves"}, "encode": {"update": {
            "x": {"signal": "datum.x0 + 5"}, "y": {"signal": "datum.y0 + 6"}, "baseline": {"value": "top"},
            "text": {"signal": "datum.x1 - datum.x0 >= 45 && datum.y1 - datum.y0 >= 20 ? datum.name : ''"},
            "fontSize": {"value": 12}, "fill": {"signal": "datum.price === 'Budget' ? '#183b35' : '#ffffff'"},
            "limit": {"signal": "max(0, datum.x1 - datum.x0 - 10)"},
        }}},
        {"type": "text", "interactive": False, "from": {"data": "leaves"}, "encode": {"update": {
            "x": {"signal": "datum.x0 + 5"}, "y": {"signal": "datum.y0 + 24"}, "baseline": {"value": "top"},
            "text": {"signal": "datum.x1 - datum.x0 >= 48 && datum.y1 - datum.y0 >= 42 ? format(datum.review_count, ',.0f') : ''"},
            "fontSize": {"value": 12}, "fill": {"signal": "datum.price === 'Budget' ? '#183b35' : '#ffffff'"},
            "limit": {"signal": "max(0, datum.x1 - datum.x0 - 10)"},
        }}},
    ],
})
write("10-review-treemap.vg.json", tree)

venn = copy.deepcopy(native)
venn["height"] = 320
venn.update({
    "description": "Three-set Venn diagram of the explicit Vegetarian friendly, Vegan options and Gluten free options listing labels. Circle areas are schematic and NOT proportional. The seven displayed values are exact mutually exclusive intersections, including zero cells. Listings with none of these recorded labels are reported outside the circles as unrecorded, not as unavailable.",
    "signals": [{"name": "unit", "update": "min(width, height - 35)"},
                {"name": "left", "update": "(width - unit) / 2"},
                {"name": "top", "value": 6}],
    "data": [
        {"name": "raw", "url": REVIEW_URL, "format": {"type": "json"}, "transform": [
            {"type": "formula", "as": "mask", "expr": "(datum.vegetarian_listed ? 4 : 0) + (datum.vegan_listed ? 2 : 0) + (datum.gluten_free_listed ? 1 : 0)"},
        ]},
        {"name": "intersections", "source": "raw", "transform": [
            {"type": "aggregate", "groupby": ["mask"], "fields": [None, "name"], "ops": ["count", "values"], "as": ["count", "members"]},
        ]},
        {"name": "circles", "values": [
            {"set": "Vegetarian", "x": 0.36, "y": 0.38, "fill": "#28746b"},
            {"set": "Vegan", "x": 0.64, "y": 0.38, "fill": "#d5a245"},
            {"set": "Gluten free", "x": 0.5, "y": 0.62, "fill": "#a65a3c"},
        ]},
        {"name": "regions", "values": [
            {"mask": 4, "label": "Vegetarian only", "x": 0.23, "y": 0.34},
            {"mask": 2, "label": "Vegan only", "x": 0.77, "y": 0.34},
            {"mask": 1, "label": "Gluten free only", "x": 0.5, "y": 0.79},
            {"mask": 6, "label": "Vegetarian + vegan only", "x": 0.5, "y": 0.235},
            {"mask": 5, "label": "Vegetarian + gluten free only", "x": 0.34, "y": 0.595},
            {"mask": 3, "label": "Vegan + gluten free only", "x": 0.66, "y": 0.595},
            {"mask": 7, "label": "All three listed labels", "x": 0.5, "y": 0.46},
            {"mask": 0, "label": "None of the three labels recorded", "x": 0.5, "y": 1.035},
        ], "transform": [
            {"type": "lookup", "from": "intersections", "key": "mask", "fields": ["mask"], "values": ["count", "members"], "as": ["count", "members"]},
            {"type": "formula", "as": "count", "expr": "isValid(datum.count) ? datum.count : 0"},
        ]},
        {"name": "labels", "values": [
            {"label": "Vegetarian", "x": 0.2, "y": 0.025},
            {"label": "Vegan", "x": 0.8, "y": 0.025},
            {"label": "Gluten free", "x": 0.5, "y": 0.965},
        ]},
    ],
    "marks": [
        {"type": "arc", "from": {"data": "circles"}, "encode": {"update": {
            "x": {"signal": "left + unit * datum.x"}, "y": {"signal": "top + unit * datum.y"},
            "innerRadius": {"value": 0}, "outerRadius": {"signal": "unit * 0.30"},
            "startAngle": {"value": 0}, "endAngle": {"signal": "2 * PI"},
            "fill": {"field": "fill"}, "fillOpacity": {"value": 0.13}, "stroke": {"field": "fill"}, "strokeWidth": {"value": 1.5},
        }}},
        {"type": "text", "from": {"data": "labels"}, "encode": {"update": {
            "x": {"signal": "left + unit * datum.x"}, "y": {"signal": "top + unit * datum.y"},
            "text": {"field": "label"}, "align": {"value": "center"}, "baseline": {"value": "middle"}, "fontSize": {"value": 12},
        }}},
        {"type": "text", "from": {"data": "regions"}, "encode": {"update": {
            "x": {"signal": "left + unit * datum.x"}, "y": {"signal": "top + unit * datum.y"},
            "text": {"signal": "datum.mask === 0 ? 'Unrecorded: ' + datum.count : datum.count"},
            "align": {"value": "center"}, "baseline": {"value": "middle"},
            "fontSize": {"signal": "datum.mask === 0 ? 12 : 18"}, "fontWeight": {"signal": "datum.mask === 0 ? 'normal' : 'bold'"},
            "tooltip": {"signal": "{'Exact combination': datum.label, 'Restaurants': datum.count, 'Listings': datum.members ? join(pluck(datum.members, 'name'), ', ') : 'No sampled listing'}"},
        }}},
    ],
})
write("11-diet-overlap.vg.json", venn)

write("12-shortlist.vl.json", vl(
    "Up to ten injected listings, ordered by rating descending, then cumulative review count descending, then name alphabetically. Review count is only a tie-breaking display rule and does not validate score reliability. Equal scores remain visually equal. The host supplies rows matching shared controls and the scatter brush. Rating axis deliberately zoomed to 4–5.",
    310, data={"name": "reviews", "values": []},
    transform=[
        {"window": [{"op": "row_number", "as": "display_order"}],
         "sort": [{"field": "rating", "order": "descending"}, {"field": "review_count", "order": "descending"}, {"field": "name", "order": "ascending"}]},
        {"filter": "datum.display_order <= 10"},
    ],
    encoding={
        "y": {"field": "name", "type": "nominal", "title": None, "sort": {"field": "display_order", "order": "ascending"},
              "axis": {"labelLimit": 220, "labelPadding": 10, "ticks": False, "domain": False}},
        "x": {"field": "rating", "type": "quantitative", "title": "Rating / 5 (zoomed)", "scale": RATING_SCALE,
              "axis": {"values": [4, 4.2, 4.4, 4.6, 4.8, 5], "format": ".1f"}},
        "tooltip": SOURCE_TOOLTIP,
    },
    layer=[
        {"mark": {"type": "rule", "color": "#d6dfd6", "strokeWidth": 1.5}, "encoding": {"x2": {"datum": 4}}},
        {"mark": {"type": "point", "filled": True, "size": 100, "stroke": "#fffdf7", "strokeWidth": 1}, "encoding": {"color": PRICE_COLOR}},
        {"mark": {"type": "text", "align": "left", "dx": 10, "fontSize": 12, "color": INK},
         "encoding": {"text": {"field": "rating", "type": "quantitative", "format": ".1f"}}},
    ],
))

print(f"Wrote 12 chart specifications to {OUT}")
