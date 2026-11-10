"""Build data/rankings.json for the next-costco site.
Inputs (raw/): ACS via Census Reporter, Census gazetteers, CBSA delineation, OSM Costco locations."""
import json, glob, csv, math, collections, sys
import openpyxl

def hav(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 7918 * math.asin(math.sqrt(x))  # miles (2R, R=3959)

# --- Costco warehouses (OSM, shop=wholesale), de-duplicated
els = json.load(open("raw/costco_osm.json"))["elements"]
cos = []
for e in els:
    t = e["tags"]
    if t.get("shop") != "wholesale": continue
    lat = e.get("lat") or e["center"]["lat"]; lon = e.get("lon") or e["center"]["lon"]
    if any(abs(lat - c[0]) < .005 and abs(lon - c[1]) < .005 for c in cos): continue
    cos.append((lat, lon, t.get("name", "Costco"), t.get("addr:city", "")))
print("warehouses", len(cos), file=sys.stderr)

# --- competing warehouse clubs (Sam's Club, BJ's), stores only, de-duplicated per brand
comps = []  # (lat, lon, brand_idx)  0=Sam's Club 1=BJ's
for e in json.load(open("raw/competitors_osm.json"))["elements"]:
    t = e["tags"]
    if t.get("shop") not in ("wholesale", "supermarket"): continue
    nm = (t.get("brand") or t.get("name") or "").lower().replace("\u2019", "'")
    b = 0 if nm.startswith("sam") else 1 if nm.startswith("bj") else None
    if b is None: continue
    lat = e.get("lat") or e["center"]["lat"]; lon = e.get("lon") or e["center"]["lon"]
    if any(c[2] == b and abs(lat - c[0]) < .005 and abs(lon - c[1]) < .005 for c in comps): continue
    comps.append((lat, lon, b))
BRANDS = ["Sam's Club", "BJ's"]
print("competitors", len(comps), file=sys.stderr)

# --- counties -> CBSA
cb = {}
ws = openpyxl.load_workbook("raw/geo/list1_2023.xlsx").active
for r in list(ws.iter_rows(values_only=True))[3:]:
    if r[0] and r[9] and r[10] and r[4] and r[4].startswith("Metro"):
        cb[r[9] + r[10]] = (r[3], r[0])
counties = []
for row in csv.reader(open("raw/geo/2024_Gaz_counties_national.txt"), delimiter="\t"):
    if row[0] == "USPS": continue
    counties.append((row[1], float(row[8]), float(row[9]), row[0]))

# --- places
gaz = {}
for row in csv.reader(open("raw/geo/2024_Gaz_place_national.txt"), delimiter="\t"):
    if row[0] == "USPS": continue
    gaz[row[1].strip()] = dict(st=row[0], name=row[3].strip(), sqmi=float(row[8]), wsqmi=float(row[9]), lat=float(row[10]), lon=float(row[11]))

places = []
for f in sorted(glob.glob("raw/acs/*.json")):
    for gid, t in json.load(open(f))["data"].items():
        g = gaz.get(gid[7:])
        if not g or g["wsqmi"] > 2 * g["sqmi"]: continue  # water-dominated: centroid unreliable
        pop = t["B01003"]["estimate"]["B01003001"]; inc = t["B19013"]["estimate"]["B19013001"]
        e = t["B15003"]["estimate"]; tot = e["B15003001"]
        if not pop or not inc or not tot or g["sqmi"] <= 0: continue
        ba = sum(e["B15003" + k] for k in ("022", "023", "024", "025")) / tot
        o = t["B25003"]["estimate"]; own = o["B25003002"] / o["B25003001"] if o["B25003001"] else None
        places.append(dict(id=gid[7:], name=g["name"], state=g["st"], lat=g["lat"], lon=g["lon"], pop=int(pop),
                           density=round(pop / g["sqmi"]), income=int(inc), ba=round(ba, 3), own=round(own, 3) if own else None,
                           age=t["B01002"]["estimate"]["B01002001"]))
print("places", len(places), file=sys.stderr)

for p in places:
    d, i = min((hav(p["lat"], p["lon"], c[0], c[1]), j) for j, c in enumerate(cos))
    cd_, ci = min((hav(p["lat"], p["lon"], c[0], c[1]), j) for j, c in enumerate(comps))
    p["comp_mi"] = round(cd_, 1); p["comp"] = BRANDS[comps[ci][2]]
    p["nearest_mi"] = round(d, 1); p["nearest"] = f"{cos[i][3] or cos[i][2]}"
    cd = min(counties, key=lambda c: hav(p["lat"], p["lon"], c[1], c[2]) if c[3] == p["state"] else 1e9)
    m = cb.get(cd[0]); p["metro"] = m[0] if m else None; p["cbsa"] = m[1] if m else None

# Metro stats: population & warehouse count
mpop = collections.Counter(); mco = collections.Counter()
for p in places:
    if p["cbsa"]: mpop[p["cbsa"]] += p["pop"]
for c in cos:
    j = min(places, key=lambda p: hav(c[0], c[1], p["lat"], p["lon"]))
    if j["cbsa"]: mco[j["cbsa"]] += 1

# Underserved catchment: pop of places within 10mi that are >10mi from any Costco
under = [p for p in places if p["nearest_mi"] >= 10]
for p in places:
    p["catch"] = int(sum(q["pop"] for q in under if abs(q["lat"] - p["lat"]) < .3 and hav(p["lat"], p["lon"], q["lat"], q["lon"]) <= 10)) if p["nearest_mi"] >= 5 else 0
    p["metro_pop"] = mpop.get(p["cbsa"], 0); p["metro_costcos"] = mco.get(p["cbsa"], 0)
    p["pop_per_costco"] = round(p["metro_pop"] / max(p["metro_costcos"], 1)) if p["cbsa"] else None

# --- scoring (each component 0-100, weighted)
def ramp(x, lo, hi): return max(0, min(1, (x - lo) / (hi - lo)))
def tent(x, lo, a, b, hi): return ramp(x, lo, a) if x < a else (1 if x <= b else 1 - ramp(x, b, hi))
W = dict(gap=.22, catch=.18, income=.18, edu=.09, density=.09, metro=.09, own=.05, comp=.10)
for p in places:
    c = dict(
        gap=ramp(p["nearest_mi"], 6, 25),                    # distance to nearest warehouse
        catch=ramp(math.log10(max(p["catch"], 1)), 4.4, 5.6),  # underserved people within 10 mi (25k..400k)
        income=ramp(p["income"], 60000, 130000),
        edu=ramp(p["ba"], .20, .55),
        density=tent(p["density"], 300, 1500, 5000, 12000),   # suburban sweet spot
        metro=ramp(p["pop_per_costco"] or 0, 150000, 450000) if p["cbsa"] else 0.15,
        own=ramp(p["own"] or 0, .45, .75),
        comp=tent(p["comp_mi"], 0, 4, 18, 45))              # proven club demand nearby, but not head-to-head
    p["components"] = {k: round(v * 100, 2) for k, v in c.items()}
    p["score"] = 100 * sum(W[k] * c[k] for k in W)

cand = sorted([p for p in places if p["pop"] >= 40000 and p["nearest_mi"] >= 8], key=lambda p: -p["score"])
top = []
for p in cand:  # greedy de-dup: one pick per ~20 miles so the list isn't one cluster
    if all(hav(p["lat"], p["lon"], q["lat"], q["lon"]) > 20 for q in top): top.append(p)
    if len(top) == 50: break
for i, p in enumerate(top, 1): p["rank"] = i
KEEP = ("comp_mi","comp","id","name","state","lat","lon","pop","income","ba","density","nearest_mi","nearest","catch","metro","metro_costcos","metro_pop","pop_per_costco","age","own","components")
for p in cand: p.setdefault("rank", None)
json.dump(dict(generated="2026-11-10", weights=W, warehouses=len(cos), candidates=len(cand),
               places=[{k: p.get(k) for k in KEEP + ("rank",)} for p in cand],
               costcos=[[round(c[0], 4), round(c[1], 4)] for c in cos],
               competitors=[[round(c[0], 4), round(c[1], 4), c[2]] for c in comps], brands=BRANDS), open("data/rankings.json", "w"), separators=(",", ":"))
for p in top: print(p["rank"], p["name"], p["state"], p["score"], p["pop"], p["income"], p["nearest_mi"], p["metro"], p["catch"])
