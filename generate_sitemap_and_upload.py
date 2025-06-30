import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
import paramiko
import os

# === CONFIGURATION ===
SOURCE_URL = "https://ccn-openpaye-roseyemeli.replit.app"
LOCAL_SITEMAP = "sitemap.xml"
REMOTE_PATH = "/var/www/html/ccn-roseyemeli/sitemap.xml"
DOMAIN = "ccn-openpaye-roseyemeli.replit.app"

# === SFTP CONFIG
SFTP_HOST = "173.199.70.178"
SFTP_PORT = 22
SFTP_USER = "root"
SFTP_PASS = "os.environ.get("SFTP_PASS")"

def extract_idccs():
    response = requests.get(SOURCE_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    idccs = set()
    for el in soup.find_all(string=lambda t: t and "IDCC" in t.upper()):
        parts = el.upper().split("IDCC")
        for part in parts[1:]:
            num = ''.join(filter(str.isdigit, part.strip().split()[0]))
            if num.isdigit():
                idccs.add(num)
    return sorted(idccs)

def generate_sitemap(idccs):
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

def upload_sitemap():
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.put(LOCAL_SITEMAP, REMOTE_PATH)
    sftp.close()
    transport.close()

if __name__ == "__main__":
    idccs = extract_idccs()
    generate_sitemap(idccs)
    upload_sitemap()
