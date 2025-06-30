# generate_sitemap.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://ccn-openpaye-roseyemeli.replit.app"
SITEMAP_FILE = "sitemap.xml"

def extract_idccs():
    r = requests.get(BASE_URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    idccs = set()
    for el in soup.find_all(string=lambda text: text and "IDCC" in text.upper()):
        parts = el.upper().split("IDCC")
        for part in parts[1:]:
            num = ''.join(filter(str.isdigit, part.strip().split()[0]))
            if num.isdigit():
                idccs.add(num)
    return sorted(idccs)

def generate_sitemap(idccs):
    today = datetime.utcnow().date().isoformat()
    with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url>\n    <loc>{BASE_URL}/</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>\n')
        for idcc in idccs:
            f.write(f'  <url>\n    <loc>{BASE_URL}/convention/{idcc}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>\n')
        f.write('</urlset>\n')

if __name__ == "__main__":
    idccs = extract_idccs()
    generate_sitemap(idccs)
