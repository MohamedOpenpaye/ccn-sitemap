import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
import paramiko
import os
import re

# === CONFIGURATION ===
SOURCE_URL = "https://ccn-openpaye-roseyemeli.replit.app"
LOCAL_SITEMAP = "sitemap.xml"
REMOTE_PATH = "/var/www/html/ccn-roseyemeli/sitemap.xml"
DOMAIN = "ccn-openpaye-roseyemeli.replit.app"

# === SFTP CONFIG
SFTP_HOST = "173.199.70.178"
SFTP_PORT = 22
SFTP_USER = "root"
SFTP_PASS = os.environ.get("SFTP_PASS")  # <- sécurisé via GitHub Secrets

def extract_idccs():
    print(f"🟡 Récupération des IDCC depuis {SOURCE_URL}")
    r = requests.get(SOURCE_URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    idccs = set()

    for tag in soup.find_all(text=True):
        if "IDCC" in tag.upper():
            matches = re.findall(r'IDCC\s*(\d{2,5})', tag.upper())
            for match in matches:
                idccs.add(match)

    idccs_sorted = sorted(idccs)
    print(f"🟢 IDCCs trouvés : {idccs_sorted}")
    return idccs_sorted

def generate_sitemap(idccs):
    print("🛠️ Génération du sitemap.xml...")
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Page d'accueil
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
    print(f"✅ Sitemap généré avec {len(idccs)} IDCC → {LOCAL_SITEMAP}")

def upload_sitemap():
    print(f"📡 Connexion au serveur SFTP {SFTP_HOST}...")
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)

    # Créer le dossier distant s’il n’existe pas
    try:
        sftp.stat("/var/www/html/ccn-roseyemeli")
    except FileNotFoundError:
        sftp.mkdir("/var/www/html/ccn-roseyemeli")

    sftp.put(LOCAL_SITEMAP, REMOTE_PATH)
    sftp.close()
    transport.close()
    print(f"🟢 sitemap.xml uploadé avec succès sur {REMOTE_PATH}")

if __name__ == "__main__":
    idccs = extract_idccs()
    generate_sitemap(idccs)
    upload_sitemap()
