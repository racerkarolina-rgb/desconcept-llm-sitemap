import requests
import gzip
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

SITEMAP_URL = "https://desconcept.pl/sitemap.xml.gz"
OUTPUT_FILE = "sitemap-llm.xml"

MAX_PER_CATEGORY = 10

CATEGORY_MAP = {
    "miska-wc": "WC",
    "wc": "WC",
    "umywalka": "Washbasins",
    "prysznic": "Shower",
    "zestaw-prysznicowy": "Shower Sets",
    "szafka": "Furniture",
    "meble": "Furniture",
    "zlewozmywak": "Kitchen Sinks",
    "zlew": "Kitchen Sinks",
    "lampa": "Lighting",
    "oswietlenie": "Lighting"
}

def download_sitemap():
    response = requests.get(SITEMAP_URL)
    return gzip.decompress(response.content)

def detect_category(url):
    for key, value in CATEGORY_MAP.items():
        if key in url.lower():
            return value
    return "Other"

def parse_products(xml_data):
    root = ET.fromstring(xml_data)
    categories = defaultdict(list)

    for url in root.findall(".//{*}url"):
        loc = url.find("{*}loc")
        if loc is not None:
            link = loc.text
            if "/products/" in link:
                cat = detect_category(link)
                if len(categories[cat]) < MAX_PER_CATEGORY:
                    categories[cat].append(link)

    return categories

def format_name(url):
    name = url.split("/")[-1].replace(".html", "").replace("-", " ")
    return name.capitalize()

def generate_xml(categories):
    today = datetime.today().strftime("%Y-%m-%d")

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<sitemap>
'''

    for category, urls in categories.items():
        xml += f'\n  <category name="{category}">\n'

        for url in urls:
            xml += f'''
    <product>
      <name>{format_name(url)}</name>
      <url>{url}</url>
      <lastmod>{today}</lastmod>
    </product>
'''

        xml += "  </category>\n"

    xml += "\n</sitemap>"
    return xml

def main():
    xml_data = download_sitemap()
    categories = parse_products(xml_data)
    content = generate_xml(categories)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
