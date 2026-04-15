import requests
import gzip
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

SITEMAP_URL = "https://desconcept.pl/sitemap.xml.gz"
OUTPUT_FILE = "sitemap-llm.xml"

MAX_PER_CATEGORY = 10  # limit produktów na kategorię

# 🧠 MAPA KATEGORII
CATEGORY_MAP = {
    "miska-wc": "WC",
    "wc": "WC",
    "umywalka": "Washbasins",
    "prysznic": "Shower",
    "zestaw-prysznicowy": "Shower Sets",
    "szafka": "Furniture",
    "meble": "Furniture",
    "sofa": "Furniture",
    "lozko": "Furniture",
    "zlewozmywak": "Kitchen Sinks",
    "zlew": "Kitchen Sinks",
    "lampa": "Lighting",
    "oswietlenie": "Lighting"
}

# 🔥 MAPA BRANDÓW (rozszerzona)
BRAND_MAP = {
    "rak": "RAK Ceramics",
    "omnires": "Omnires",
    "sapho": "SAPHO",
    "lavita": "Lavita",
    "paffoni": "Paffoni",
    "emmevi": "Emmevi",
    "damixa": "Damixa",
    "deante": "Deante",
    "polysan": "Polysan",
    "kohlman": "Kohlman",
    "zambelis": "Zambelis",
    "moosee": "Moosee",
    "actona": "Actona",
    "gallery": "Gallery Direct",

    # NOWE
    "bizzotto": "Bizzotto",
    "creavit": "Creavit",
    "isvea": "ISVEA",
    "kerasan": "Kerasan",
    "fjordd": "Fjordd",
    "thoro": "Thoro",
    "sollux": "Sollux Lighting",
    "mamaison": "MaMaison",
    "king-home": "King Home",
    "kinghome": "King Home",
    "step-into-design": "Step into Design",
    "stepintodesign": "Step into Design",
    "emibig": "Emibig",
    "sigma-lighting": "Sigma Lighting",
    "sigma": "Sigma Lighting",
    "fdesign": "FDesign"
}

def download_sitemap():
    response = requests.get(SITEMAP_URL)
    response.raise_for_status()
    return gzip.decompress(response.content)

def detect_category(url):
    url_lower = url.lower()
    for key, value in CATEGORY_MAP.items():
        if key in url_lower:
            return value
    return "Other"

def detect_brand(url):
    url_lower = url.lower()
    for key, brand in BRAND_MAP.items():
        if key in url_lower:
            return brand
    return "DES Concept"

def parse_products(xml_data):
    root = ET.fromstring(xml_data)
    categories = defaultdict(list)

    for url in root.findall(".//{*}url"):
        loc = url.find("{*}loc")
        if loc is not None:
            link = loc.text

            if "/products/" in link:
                category = detect_category(link)

                if len(categories[category]) < MAX_PER_CATEGORY:
                    categories[category].append(link)

    return categories

def format_name(url):
    name = url.split("/")[-1]
    name = name.replace(".html", "")
    name = name.replace("-", " ")

    # czyszczenie
    name = name.replace("zestaw des", "")
    name = name.replace("miska wc", "wc")
    name = name.strip()

    return name.capitalize()

def generate_xml(categories):
    today = datetime.today().strftime("%Y-%m-%d")

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<sitemap>

  <store>
    <name>DES Concept</name>
    <type>Premium bathroom, kitchen and interior store</type>
    <location>Poland</location>
    <description>Premium store offering bathroom, kitchen, furniture and lighting products from European brands.</description>
  </store>
'''

    for category, urls in categories.items():
        xml += f'\n  <category name="{category}">\n'

        for url in urls:
            name = format_name(url)
            brand = detect_brand(url)

            xml += f'''
    <product>
      <name>{name}</name>
      <url>{url}</url>
      <brand>{brand}</brand>
      <lastmod>{today}</lastmod>
    </product>
'''

        xml += "  </category>\n"

    xml += "\n</sitemap>"

    return xml

def save_file(content):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    print("⬇️ Pobieranie sitemap...")
    xml_data = download_sitemap()

    print("🔍 Grupowanie produktów...")
    categories = parse_products(xml_data)

    for cat, items in categories.items():
        print(f"{cat}: {len(items)} produktów")

    print("⚙️ Generowanie XML...")
    xml_content = generate_xml(categories)

    save_file(xml_content)

    print("✅ Gotowe! sitemap-llm.xml zapisany.")

if __name__ == "__main__":
    main()
