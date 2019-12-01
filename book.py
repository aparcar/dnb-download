from fpdf import FPDF
from multiprocessing import Pool
from random import randint
from urllib import request
import os
import re
import sys
import time

# die buch id bestehend nur aus zahlen
if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <book_id>")
    exit(1)

book_id = sys.argv[1]

base_url = "https://portal.dnb.de/bookviewer/view"
book_path = "./dl/{}".format(book_id)

# html runterladen
html = request.urlopen("{}/{}".format(base_url, book_id)).read().decode("utf-8")
# titel parsen
book_title = re.search(r".*br.bookTitle=.'(.+?)'", html, re.MULTILINE).group(1)
# einen sinvollen dateinamen bauen
book_title_sani = book_title.strip().lower().replace(" ", "_")
# anzahl der seiten parsen
book_pages = int(re.search(r"br.numLeafs = (\d+);", html, re.MULTILINE).group(1))
# breite parsen
book_width = int(re.search(r"br.pageW = \[(\d+),", html, re.MULTILINE).group(1))
# hoehe parsen
book_height = int(re.search(r"br.pageH = \[(\d+),", html, re.MULTILINE).group(1))

print(
    "Found '{}' with {} pages ({} x {})".format(
        book_title, book_pages, book_width, book_height
    )
)


# function um seite runterzuladen
def download_page(page):
    # dateipfad bauen
    page_path = "{}/{}.jpg".format(book_path, page)
    # nur runterladen wenn noch nicht runtergeladen
    if not os.path.exists(page_path):
        # url bauen
        image_url = "{}/{}/img/page/{:03d}/p.jpg".format(base_url, book_id, page)
        print("Downloading page {} from {}".format(page, image_url))
        # image runterladen
        image = request.urlopen(image_url).read()
        # image abspeichern
        with open(page_path, "wb") as image_file:
            image_file.write(image)

        # kurz warten damit der server einen nicht blockier
        time.sleep(randint(1, 10))
    else:
        print("Page {} already downloaded".format(page))


# pfad fuer bilder erstellen
os.makedirs(book_path, exist_ok=True)

# 10 seiten gleichzeitig runterladen
pool = Pool(10)
pool.map(download_page, range(1, book_pages))

# nur machen wenn pdf noch nicht existiert
if not os.path.exists(book_title_sani + ".pdf"):
    # das pdf tool
    pdf = FPDF(unit="pt", format=[book_width, book_height])

    # seiten zur pdf hinzufuegen
    for page in range(1, book_pages):
        pdf.add_page()
        pdf.image("{}/{}.jpg".format(book_path, page), 0, 0)

    # pdf abspeichern
    pdf.output(book_title_sani + ".pdf", "F")

print("PDF created at {}".format(book_title_sani + ".pdf"))
