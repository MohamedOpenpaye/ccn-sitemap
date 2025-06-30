import asyncio
from playwright.sync_api import sync_playwright, TimeoutError
from datetime import datetime
import xml.etree.ElementTree as ET
import os

SOURCE_URL = "https://ccn-openpaye-roseyemeli.replit.app"
LOCAL_SITEMAP = "sitemap.xml"  # ✅ Le sitemap est généré à la racine

def extract_idccs_with_playwright():
    print(f"🌀 Rendu JS avec Playwright pour {SOURCE_URL}")
    idccs = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SOURCE_URL, wait_until="networkidle")

        # 🕒 On attend explicitement que les liens de convention apparaissent
        try:
            page.wait_for_selector("a[href^='/convention/']", timeout=10000)
        except TimeoutError:
            print("⚠️ Aucun lien /convention/ trouvé après 10 secondes.")
            browser.close()
            return []

        # 🔁 Scroll infini (au cas où)
        previous_height = 0
        max_scrolls = 30
        scroll_count = 0
        while scroll_count < max_scrolls:
            current_height = page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                break
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(800)
            previous_height = current_height
            scroll_count += 1

        # ✅ Extraction des liens
        links = page.query_selector_all("a[href^='/convention/']")
        for link in links:
            href = link.get_attribute("href")
            if href:
                idcc = href.split("/convention/")[1].split("/")[0]
                if idcc.isdigit():
                    idccs.add(idcc)

        browser.close()

    idccs_sorted = sorted(idccs)
    print(f"✅ {len(idccs_sorted)} IDCCs trouvés : {idccs_sorted[:10]}...")
    return idccs_sorted


def generate_sitemap(idccs):
    print("📄 Génération du sitemap.xml...")
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    url = ET.SubElement(urlset, "url")
    ET.SubElement(url, "loc").text = SOURCE_URL + "/"
    ET.SubElement(url, "lastmod").text = today
    ET.SubElement(url, "changefreq").text = "weekly"
    ET.SubElement(url, "priority").text = "1.0"

    for idcc in idccs:
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = f"{SOURCE_URL}/convention/{idcc}"
        ET.SubElement(url, "lastmod").text = today
        ET.SubElement(url, "changefreq").text = "weekly"
        ET.SubElement(url, "priority").text = "0.8"

    tree = ET.ElementTree(urlset)
    tree.write(LOCAL_SITEMAP, encoding="utf-8", xml_declaration=True)
    print(f"📦 sitemap.xml généré avec {len(idccs)} entrées.")


if __name__ == "__main__":
    idccs = extract_idccs_with_playwright()
    generate_sitemap(idccs)
