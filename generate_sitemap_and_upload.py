import asyncio
from playwright.sync_api import sync_playwright
from datetime import datetime
import xml.etree.ElementTree as ET
import paramiko
import os

SOURCE_URL = "https://ccn-openpaye-roseyemeli.replit.app"
LOCAL_SITEMAP = "sitemap.xml"
REMOTE_PATH = "/var/www/html/ccn-roseyemeli/sitemap.xml"
SFTP_HOST = "173.199.70.178"
SFTP_PORT = 22
SFTP_USER = "root"
SFTP_PASS = os.environ.get("SFTP_PASS")

def extract_idccs_with_playwright():
    print(f"🌀 Rendu JS avec Playwright pour {SOURCE_URL}")
    idccs = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SOURCE_URL, wait_until="networkidle")

        links = page.query_selector_all("a[href^='/convention/']")
        for link in links:
            href = link.get_attribute("href")
            if href:
                idcc = href.split("/convention/")[1].split("/")[0]
                if idcc.isdigit():
                    idccs.add(idcc)

        browser.close()

    idccs_sorted = sorted(idccs)
    print(f"✅ {len(idccs_sorted)} IDCCs trouvés : {idccs_sorted[:5]}...")
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

def upload_sitemap():
    print(f"📤 Connexion SFTP à {SFTP_HOST}...")
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)

    try:
        sftp.stat("/var/www/html/ccn-roseyemeli")
    except FileNotFoundError:
        sftp.mkdir("/var/www/html/ccn-roseyemeli")

    sftp.put(LOCAL_SITEMAP, REMOTE_PATH)
    sftp.close()
    transport.close()
    print("✅ sitemap.xml uploadé avec succès.")

if __name__ == "__main__":
    idccs = extract_idccs_with_playwright()
    generate_sitemap(idccs)
    upload_sitemap()
