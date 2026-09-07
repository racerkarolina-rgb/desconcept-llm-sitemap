#!/usr/bin/env python3
"""Build the DES Concept OpenAI Ads feed from IdoSell and upload it to SFTP."""

import csv
import gzip
import html
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import paramiko
import requests

SOURCE_URL = "https://desconcept.pl/data/export/googleshoppingpl_1ae84569e8b4d9b58852f39d.xml"
REMOTE_FILENAME = "DES_Concept_OpenAI_Ads_products.csv.gz"
G = "{http://base.google.com/ns/1.0}"
FIELDS = [
    "item_id", "title", "description", "url", "brand", "seller_name",
    "image_url", "additional_image_urls", "availability", "price",
    "sale_price", "condition", "product_category", "gtin", "mpn",
    "is_ads_eligible",
]


def clean_text(value):
    value = html.unescape(value or "").replace("\xa0", " ")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def text(item, tag):
    node = item.find(tag)
    return (node.text or "").strip() if node is not None else ""


def availability(value):
    key = re.sub(r"[\s-]+", "_", (value or "").strip().lower())
    return {
        "in_stock": "in_stock", "out_of_stock": "out_of_stock",
        "preorder": "pre_order", "pre_order": "pre_order",
        "backorder": "backorder", "unknown": "unknown",
    }.get(key, "unknown")


def money(value):
    match = re.search(r"(-?\d+(?:[.,]\d+)?)\s*([A-Za-z]{3})", value or "")
    return f"{match.group(1).replace(',', '.')} {match.group(2).upper()}" if match else ""


def gtin(value):
    digits = re.sub(r"\D", "", value or "")
    if len(digits) not in {8, 12, 13, 14}:
        return ""
    total = sum(int(d) * (3 if i % 2 == 0 else 1)
                for i, d in enumerate(reversed(digits[:-1])))
    return digits if (10 - total % 10) % 10 == int(digits[-1]) else ""


def download(destination):
    with requests.get(SOURCE_URL, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with destination.open("wb") as output:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    output.write(chunk)


def convert(source, destination):
    stats = {"seen": 0, "written": 0, "duplicates": 0, "missing_required": 0}
    seen_ids = set()
    with gzip.open(destination, "wt", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDS)
        writer.writeheader()
        for _, item in ET.iterparse(source, events=("end",)):
            if item.tag != "item":
                continue
            stats["seen"] += 1
            item_id = text(item, G + "id")
            if item_id in seen_ids:
                stats["duplicates"] += 1
                item.clear()
                continue
            seen_ids.add(item_id)
            product_types = [clean_text(n.text or "") for n in item.findall(G + "product_type")]
            row = {
                "item_id": item_id,
                "title": clean_text(text(item, "title"))[:150],
                "description": clean_text(text(item, "description"))[:5000],
                "url": text(item, "link"),
                "brand": clean_text(text(item, G + "brand")),
                "seller_name": "DES Concept",
                "image_url": text(item, G + "image_link"),
                "additional_image_urls": ",".join(
                    (node.text or "").strip()
                    for node in item.findall(G + "additional_image_link")
                    if (node.text or "").strip()
                ),
                "availability": availability(text(item, G + "availability")),
                "price": money(text(item, G + "price")),
                "sale_price": money(text(item, G + "sale_price")),
                "condition": text(item, G + "condition") or "new",
                "product_category": product_types[0] if product_types else "",
                "gtin": gtin(text(item, G + "gtin")),
                "mpn": text(item, G + "mpn"),
                "is_ads_eligible": "true",
            }
            if not row["description"] and row["title"] and row["brand"]:
                row["description"] = f"{row['title']} marki {row['brand']}, dostępny w sklepie DES Concept."
            required = ("item_id", "title", "description", "url", "brand",
                        "seller_name", "image_url", "availability", "price")
            if not all(row[field] for field in required):
                stats["missing_required"] += 1
            else:
                writer.writerow(row)
                stats["written"] += 1
            item.clear()
    return stats


def upload(local_file):
    host = os.environ["OPENAI_SFTP_HOST"]
    port = int(os.environ.get("OPENAI_SFTP_PORT", "443"))
    username = os.environ["OPENAI_SFTP_USERNAME"]
    password = os.environ["OPENAI_SFTP_PASSWORD"]
    transport = paramiko.Transport((host, port))
    try:
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        try:
            sftp.put(str(local_file), "/" + REMOTE_FILENAME)
        finally:
            sftp.close()
    finally:
        transport.close()


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        source = temp / "idosell.xml"
        feed = temp / REMOTE_FILENAME
        download(source)
        stats = convert(source, feed)
        if stats["written"] < 1000:
            raise RuntimeError(f"Safety stop: only {stats['written']} valid products")
        upload(feed)
        print(f"Uploaded {feed.name}: {stats}")


if __name__ == "__main__":
    main()
