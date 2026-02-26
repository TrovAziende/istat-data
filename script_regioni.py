import requests
from lxml import etree
import json
from datetime import datetime
import re

current_year = datetime.now().year

pop_start = current_year - 5
pop_end   = current_year

regioni_info = {
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

def fetch_sdmx(url):
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    root = etree.fromstring(response.content)
    ns = {"g": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"}
    return root, ns

print("Scarico popolazione regioni...")

nuts_list = "+".join(regioni_info.keys())

url = (
    "https://esploradati.istat.it/SDMXWS/rest/data/"
    "IT1,22_289_DF_DCIS_POPRES1_1,1.0/"
    f"A.{nuts_list}.JAN.9..99/ALL/"
    f"?detail=dataonly&startPeriod={pop_start}-01-01&endPeriod={pop_end}-12-31"
    "&dimensionAtObservation=TIME_PERIOD"
)

root, ns = fetch_sdmx(url)

dataset = {}

for series in root.xpath("//g:Series", namespaces=ns):

    nuts = series.xpath("./g:SeriesKey/g:Value[@id='REF_AREA']/@value", namespaces=ns)[0]

    if nuts not in regioni_info:
        continue

    istat, nome, slug, sup = regioni_info[nuts]

    serie = {}
    for obs in series.xpath("./g:Obs", namespaces=ns):
        anno = re.findall(r"\d{4}", obs.xpath("./g:ObsDimension/@value", namespaces=ns)[0])[0]
        val = int(float(obs.xpath("./g:ObsValue/@value", namespaces=ns)[0]))
        serie[anno] = val

    dataset[istat] = {
        "nome": nome,
        "slug": slug,
        "superficie_km2": sup,
        "popolazione": list(serie.values())[-1] if serie else None,
        "serie_popolazione": dict(sorted(serie.items()))
    }

with open("regioni.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

print("regioni.json aggiornato correttamente")
