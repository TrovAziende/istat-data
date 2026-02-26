cat <<'PYTHON' > script.py
import requests
from lxml import etree
import json
import time
from datetime import datetime

# -------------------------
# CONFIG REGIONI
# -------------------------

regioni = {
    "ITC1": ("01", "Piemonte", "piemonte", 25387),
    "ITC2": ("02", "Valle d'Aosta", "valle-daosta", 3263),
    "ITC3": ("07", "Liguria", "liguria", 5416),
    "ITC4": ("03", "Lombardia", "lombardia", 23863),
    "ITDA": ("04", "Trentino-Alto Adige", "trentino-alto-adige", 13607),
    "ITD3": ("05", "Veneto", "veneto", 18345),
    "ITD4": ("06", "Friuli-Venezia Giulia", "friuli-venezia-giulia", 7924),
    "ITD5": ("08", "Emilia-Romagna", "emilia-romagna", 22453),
    "ITE1": ("09", "Toscana", "toscana", 22987),
    "ITE2": ("10", "Umbria", "umbria", 8456),
    "ITE3": ("11", "Marche", "marche", 9366),
    "ITE4": ("12", "Lazio", "lazio", 17232),
    "ITF1": ("13", "Abruzzo", "abruzzo", 10831),
    "ITF2": ("14", "Molise", "molise", 4460),
    "ITF3": ("15", "Campania", "campania", 13671),
    "ITF4": ("16", "Puglia", "puglia", 19359),
    "ITF5": ("17", "Basilicata", "basilicata", 9992),
    "ITF6": ("18", "Calabria", "calabria", 15080),
    "ITG1": ("19", "Sicilia", "sicilia", 25711),
    "ITG2": ("20", "Sardegna", "sardegna", 24100),
}

# -------------------------
# ANNI DINAMICI (ULTIMI 5)
# -------------------------

anno_corrente = datetime.now().year
anno_inizio = anno_corrente - 4

nuts_list = "+".join(regioni.keys())

url = (
    "https://esploradati.istat.it/SDMXWS/rest/data/"
    "IT1,22_289_DF_DCIS_POPRES1_1,1.0/"
    f"A.{nuts_list}.JAN.9..99/ALL/"
    "?detail=dataonly"
    f"&startPeriod={anno_inizio}-01-01"
    f"&endPeriod={anno_corrente}-12-31"
    "&dimensionAtObservation=TIME_PERIOD"
)

# -------------------------
# FETCH CON RETRY
# -------------------------

def fetch(url):
    for i in range(3):
        try:
            print(f"Tentativo {i+1} download popolazione...")
            r = requests.get(url, timeout=180, headers={"Accept-Encoding": "gzip"})
            r.raise_for_status()
            return r.content
        except Exception as e:
            print("Errore:", e)
            time.sleep(10)
    raise Exception("Errore persistente download ISTAT")

print("Download popolazione regioni...")
xml_data = fetch(url)

# -------------------------
# PARSING XML
# -------------------------

root = etree.fromstring(xml_data)
ns = {"g": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"}

dataset = {}

for series in root.xpath("//g:Series", namespaces=ns):

    ref_area = series.xpath("./g:SeriesKey/g:Value[@id='REF_AREA']/@value", namespaces=ns)
    age = series.xpath("./g:SeriesKey/g:Value[@id='AGE']/@value", namespaces=ns)

    if not ref_area or not age:
        continue

    if age[0] != "TOTAL":
        continue

    nuts = ref_area[0]

    if nuts not in regioni:
        continue

    codice, nome, slug, superficie = regioni[nuts]

    serie = {}
    for obs in series.xpath("./g:Obs", namespaces=ns):
        anno = obs.xpath("./g:ObsDimension/@value", namespaces=ns)[0]
        valore = int(obs.xpath("./g:ObsValue/@value", namespaces=ns)[0])
        serie[anno] = valore

    serie = dict(sorted(serie.items()))

    dataset[codice] = {
        "nome": nome,
        "slug": slug,
        "superficie_km2": superficie,
        "popolazione": list(serie.values())[-1] if serie else None,
        "serie_popolazione": serie
    }

dataset = dict(sorted(dataset.items()))

with open("regioni.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

print("regioni.json aggiornato correttamente")
PYTHON
