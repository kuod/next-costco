# Next Costco

Static GitHub Pages site ranking the 50 US places most ripe for a new Costco warehouse.

**Live site: https://kuod.github.io/next-costco/**

- `index.html` – the site (no build step; Leaflet from CDN)
- `data/rankings.json` – output of the pipeline
- `scripts/fetch_acs.py` – downloads ACS 5-year place data from Census Reporter (no API key)
- `scripts/build.py` – joins ACS + Census gazetteers + CBSA delineation + OSM Costco locations and scores places

Rebuild: put the Overpass export of `brand:wikidata=Q715583` in `raw/costco_osm.json`, the Census gazetteer/delineation files in `raw/geo/`, run `fetch_acs.py`, then `build.py` (needs `openpyxl`).

Preview locally: `python3 -m http.server` and open http://localhost:8000.
Deploy: push to GitHub, then Settings → Pages → deploy from the `main` branch root.
