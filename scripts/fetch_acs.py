import json, time, urllib.request, sys, os
FIPS = ["01","02","04","05","06","08","09","10","11","12","13","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","44","45","46","47","48","49","50","51","53","54","55","56"]
TABLES = "B01003,B19013,B15003,B01002,B25003"
for f in FIPS:
    out = f"raw/acs/{f}.json"
    if os.path.exists(out): continue
    url = f"https://api.censusreporter.org/1.0/data/show/latest?table_ids={TABLES}&geo_ids=160%7C04000US{f}"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "next-costco-research/0.1"})
            data = urllib.request.urlopen(req, timeout=120).read()
            json.loads(data); open(out, "wb").write(data); print(f, len(data)); break
        except Exception as e:
            print(f, "retry", e, file=sys.stderr); time.sleep(3 * (attempt + 1))
