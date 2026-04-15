import requests
import gzip
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

SITEMAP_URL = "https://desconcept.pl/sitemap.xml.gz"
OUTPUT_FILE = "sitemap-llm.xml"
MAX_PER_CATEGORY = 15

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

# ✅ FIX: obsługa gzip + XML (IdoSell chaos)
def download_xml(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()

    content = r.content

    # sprawdzamy czy to prawdziwy gzip
    if content[:2] == b'\x1f\x8b':
        try:
            print("📦 GZIP wykryty — rozpakowuję")
            return gzip.decompress(content)
        except:
            print("⚠️ błąd gzip — używam raw")
            return content
    else:
        print("📄 zwykły XML (bez gzip)")
        return content

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

def extract_products(xml_data, categories):
    root = ET.fromstring(xml_data)

    for url in root.findall(".//{*}url"):
        loc = url.find("{*}loc")
        if loc is not None:
            link = loc.text

            if "/products/" in link:
                cat = detect_category(link)

                if len(categories[cat]) < MAX_PER_CATEGORY:
                    categories[cat].append(link)

def parse_sitemap(xml_data):
    categories = defaultdict(list)
    root = ET.fromstring(xml_data)

    urls = root.findall(".//{*}url")

    # 🔥 jeśli to sitemap index
    if not urls:
        print("📂 sitemap index wykryty")

        for sm in root.findall(".//{*}sitemap"):
            loc = sm.find("{*}loc")

            if loc is not None:
                sub_url = loc.text

                try:
                    print(f"➡️ pobieram sub-sitemap: {sub_url}")
                    sub_xml = download_xml(sub_url)
                    extract_products(sub_xml, categories)

                except Exception as e:
                    print(f"❌ błąd sub-sitemap: {e}")
    else:
        extract_products(xml_data, categories)

    return categories

def format_name(url):
    name = url.split("/")[-1]
    name = name.replace(".html", "")
    name = name.replace("-", " ")

    name = name.replace("zestaw des", "")
    name = name.replace("miska wc", "wc")

    return name.strip().capitalize()

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
    try:
        print("⬇️ Pobieranie sitemap...")
        xml_data = download_xml(SITEMAP_URL)

        print("🔍 Parsowanie...")
        categories = parse_sitemap(xml_data)

        for cat, items in categories.items():
            print(f"{cat}: {len(items)} produktów")

        print("⚙️ Generowanie XML...")
        xml_content = generate_xml(categories)

        save_file(xml_content)

        print("✅ GOTOWE — sitemap-llm.xml zapisany")

    except Exception as e:
        print(f"❌ Błąd krytyczny: {e}")

if __name__ == "__main__":
    main()
