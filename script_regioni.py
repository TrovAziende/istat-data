import requests
from lxml import etree
import json
from datetime import datetime
import re
import time

current_year = datetime.now().year

# Range dinamici
pop_start = current_year - 5
pop_end   = current_year

pil_end   = current_year - 1
pil_start = pil_end - 9

imp_end   = current_year - 1
imp_start = imp_end - 9

# ===============================
# METADATI REGIONI
# ===============================

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

# ===============================
# FUNZIONE SDMX ROBUSTA
# ===============================

def fetch_sdmx(url):
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            root = etree.fromstring(response.content)
            ns = {"g": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"}
            return root, ns
        except Exception as e:
            print(f"Tentativo {attempt+1} fallito, ritento...")
            time.sleep(5)
    raise Exception("Errore persistente nella richiesta ISTAT")

dataset = {}

# ===============================
# POPOLAZIONE
# ===============================

for nuts, (istat, nome, slug, sup) in regioni_info.items():

    print(f"Popolazione {nome}")

    url = (
        "https://esploradati.istat.it/SDMXWS/rest/data/"
        "IT1,22_289_DF_DCIS_POPRES1_1,1.0/"
        f"A.{nuts}.JAN.9..99/ALL/"
        f"?detail=dataonly&startPeriod={pop_start}-01-01&endPeriod={pop_end}-12-31"
        "&dimensionAtObservation=TIME_PERIOD"
    )

    root, ns = fetch_sdmx(url)

    serie = {}
    for obs in root.xpath("//g:Obs", namespaces=ns):
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

# ===============================
# PIL
# ===============================

for nuts, (istat, _, _, _) in regioni_info.items():

    print(f"PIL {istat}")

    url = (
        "https://esploradati.istat.it/SDMXWS/rest/data/"
        "IT1,93_498_DF_DCCN_PILT_1,1.0/"
        f"A.{nuts}...N./ALL/"
        f"?detail=dataonly&startPeriod={pil_start}-01-01&endPeriod={pil_end}-12-31"
        "&dimensionAtObservation=TIME_PERIOD"
    )

    root, ns = fetch_sdmx(url)

    serie = {}
    for obs in root.xpath("//g:Obs", namespaces=ns):
        anno = re.findall(r"\d{4}", obs.xpath("./g:ObsDimension/@value", namespaces=ns)[0])[0]
        val = float(obs.xpath("./g:ObsValue/@value", namespaces=ns)[0])
        serie[anno] = val

    dataset[istat]["pil_mln_euro"] = list(serie.values())[-1] if serie else None
    dataset[istat]["serie_pil_mln_euro"] = dict(sorted(serie.items()))

# ===============================
# IMPRESE ATTIVE
# ===============================

for nuts, (istat, _, _, _) in regioni_info.items():

    print(f"Imprese {istat}")

    url = (
        "https://esploradati.istat.it/SDMXWS/rest/data/"
        "IT1,183_277_DF_DICA_ASIAUE1P_1,1.0/"
        f"A.{nuts}.AENTN.0010.TOTAL.TOT.9./ALL/"
        f"?detail=dataonly&startPeriod={imp_start}-01-01&endPeriod={imp_end}-12-31"
        "&dimensionAtObservation=TIME_PERIOD"
    )

    root, ns = fetch_sdmx(url)

    serie = {}
    for obs in root.xpath("//g:Obs", namespaces=ns):
        anno = re.findall(r"\d{4}", obs.xpath("./g:ObsDimension/@value", namespaces=ns)[0])[0]
        val = int(float(obs.xpath("./g:ObsValue/@value", namespaces=ns)[0]))
        serie[anno] = val

    dataset[istat]["imprese_attive"] = list(serie.values())[-1] if serie else None
    dataset[istat]["serie_imprese_attive"] = dict(sorted(serie.items()))

# ===============================
# SALVATAGGIO
# ===============================

with open("regioni.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

print("regioni.json aggiornato correttamente")
