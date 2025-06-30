import asyncio
from playwright.sync_api import sync_playwright, TimeoutError
from datetime import datetime
import xml.etree.ElementTree as ET
import os
import subprocess

SOURCE_URL = "https://ccn-openpaye-smartdatapay.replit.app"
LOCAL_SITEMAP = "sitemap.xml"

def extract_idccs_and_titles():
    print(f"🌀 Extraction depuis {SOURCE_URL}")
    conventions = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SOURCE_URL, wait_until="networkidle")

        try:
            page.wait_for_selector("a[href^='/convention/']", timeout=10000)
        except TimeoutError:
            print("⚠️ Aucun lien /convention/ trouvé après 10 sec.")
            browser.close()
            return []

        previous_height = 0
        for _ in range(30):
            current_height = page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                break
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(800)
            previous_height = current_height

        links = page.query_selector_all("a[href^='/convention/']")
        for link in links:
            href = link.get_attribute("href")
            title_el = link.query_selector("h3")
            title = title_el.inner_text().strip() if title_el else ""
            if href and href.startswith("/convention/"):
                idcc = href.split("/convention/")[1].split("/")[0]
                if idcc.isdigit():
                    conventions.append({
                        "idcc": idcc,
                        "title": title,
                        "url": f"{SOURCE_URL}/convention/{idcc}"
                    })

        browser.close()

    print(f"✅ {len(conventions)} conventions extraites.")
    return conventions


def generate_sitemap(conventions):
    print("📄 Génération du sitemap.xml avec <title>...")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    url = ET.SubElement(urlset, "url")
    ET.SubElement(url, "loc").text = f"{SOURCE_URL}/"
    ET.SubElement(url, "lastmod").text = today
    ET.SubElement(url, "changefreq").text = "weekly"
    ET.SubElement(url, "priority").text = "1.0"
    ET.SubElement(url, "title").text = "Accueil"

    for conv in conventions:
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = conv["url"]
        ET.SubElement(url, "lastmod").text = today
        ET.SubElement(url, "changefreq").text = "weekly"
        ET.SubElement(url, "priority").text = "0.8"
        ET.SubElement(url, "title").text = conv["title"]

    tree = ET.ElementTree(urlset)
    tree.write(LOCAL_SITEMAP, encoding="utf-8", xml_declaration=True)
    print(f"📦 sitemap.xml généré avec {len(conventions)} conventions.")


def commit_sitemap_to_git():
    print("📁 Commit GitHub Pages...")
    subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"])
    subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"])
    subprocess.run(["git", "add", LOCAL_SITEMAP])
    subprocess.run(["git", "commit", "-m", "🔄 MAJ sitemap.xml avec <title> pour CustomGPT"])
    subprocess.run(["git", "push"])
    print("✅ sitemap.xml poussé avec balises <title>.")


if __name__ == "__main__":
    conventions = extract_idccs_and_titles()
    generate_sitemap(conventions)
    commit_sitemap_to_git()
