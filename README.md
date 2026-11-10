# Next Costco

A static GitHub Pages site ranking the 50 US places most ripe for a new Costco warehouse.

**Live site: https://kuod.github.io/next-costco/**

## What it does

- Scores every US Census place with 40,000+ residents and no Costco within 8 miles (339 places), then shows the top 50 with a map and a sortable, filterable table.
- **Reweight the priorities:** sliders for each factor re-rank the list instantly, with presets and arrows showing movement against the default ranking.
- **Map layers:** existing Costcos plus competing warehouse clubs (Sam's Club and BJ's), each toggleable.

## How places are scored

Eight components, each 0-100, combined with adjustable weights (default in parentheses):

| Component | Weight | Meaning |
|---|---|---|
| Distance to nearest Costco | 22% | Farther is better, up to about 25 mi |
| Underserved catchment | 18% | People within 10 mi in towns that are 10+ mi from any Costco |
| Median household income | 18% | ACS 5-year |
| Bachelor's degree or higher | 9% | ACS 5-year |
| Suburban density | 9% | Peaks at about 1,500-5,000 people per sq mi |
| Metro saturation | 9% | Metro people per existing Costco |
| Rival club distance | 10% | Distance to nearest Sam's Club or BJ's; peaks at 4-18 mi (rival nearby proves demand, next door means a head-to-head fight). A judgment call: set it to 0 to ignore rivals |
| Homeownership | 5% | ACS 5-year |

The top 50 are picked greedily with at least 20 miles between picks, so the list isn't one suburb cluster repeated.

## Repo layout

- `index.html`: the whole site (inline CSS/JS, no build step; Leaflet from a CDN)
- `data/rankings.json`: pipeline output (all candidates, component scores, default weights, warehouse coordinates)
- `scripts/fetch_acs.py`: downloads ACS 5-year place data from Census Reporter (no API key)
- `scripts/build.py`: joins the inputs and scores places
- `CLAUDE.md`: notes for working on the project with Claude Code

## Rebuilding the data

Inputs go in `raw/` (gitignored):

- `raw/costco_osm.json`: Overpass export of Costco (`brand:wikidata=Q715583`) in the US
- `raw/competitors_osm.json`: Overpass export of Sam's Club and BJ's stores (`shop=wholesale|supermarket`)
- `raw/geo/`: Census 2024 place and county gazetteers, and the July 2023 CBSA delineation (`list1_2023.xlsx`)
- `raw/acs/`: produced by `python3 scripts/fetch_acs.py`

Then run `python3 scripts/build.py` (needs `openpyxl`; use a virtualenv).

Preview locally with `python3 -m http.server` and open http://localhost:8000. Deployment is GitHub Pages from the `main` branch root.

## Caveats

- Costco, Sam's Club and BJ's locations come from OpenStreetMap and can lag new openings. Verify a pick against costco.com before drawing conclusions.
- Distances are straight-line from each place's Census internal point, not drive time. Places that are mostly water are excluded because their centroids are unreliable.
- Places are mapped to a metro through the nearest county centroid, so a few places near county lines may be misassigned.
- It's a screening model. It doesn't know about land, zoning, traffic or Costco's actual expansion plans.

## Data sources and licenses

- Demographics: American Community Survey 5-year estimates via [Census Reporter](https://censusreporter.org). Geography and metro delineations: US Census Bureau.
- Warehouse locations: © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, available under the [ODbL](https://opendatacommons.org/licenses/odbl/). `data/rankings.json` contains data derived from OpenStreetMap, so reuse of that file is subject to the ODbL.
- Costco, Sam's Club and BJ's are trademarks of their respective owners. This project is independent and not affiliated with them.
- The code in this repo is released under the [MIT License](LICENSE).
