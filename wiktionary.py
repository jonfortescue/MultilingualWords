import sys
import re
import argparse
from lxml import etree
from pathlib2 import Path
import bz2
import urllib2
import codecs

#############################################
# all of this can  essentially be ignored. it's just unicode compat
#
# without this, encoding issues cause errors
reload(sys)
sys.setdefaultencoding('utf-8')

# windows compat
if sys.platform == "win32":
    try:
        import uniconsole
    except ImportError:
        sys.exc_clear()  # could be just pass, of course
    else:
        del uniconsole  # reduce pollution, not needed anymore
#############################################

def is_ascii(s):
    return all(ord(char) < 128 for char in s)

def download_file(url, file_name):
    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,

    f.close()

parser = argparse.ArgumentParser(description='Parse Wiktionary dump for multilingual words')
parser.add_argument("--lang", nargs="?", default="en")
parser.add_argument("-r", "--redownload", action="store_true")
parser.add_argument("--onlyascii", action="store_true")
parser.add_argument("--nonascii", action="store_true")
parser.add_argument("--nonlatin", action="store_true")  # TODO: implement
parser.add_argument("--noletters", action="store_true")  # TODO: implement
args = parser.parse_args()

Path("dumps").mkdir(exist_ok=True)
DUMP_FILE_PATH = "dumps/%swiktionary-latest-pages-articles.xml" % args.lang
if not Path(DUMP_FILE_PATH).is_file() or args.redownload:
    print "Downloading latest %s-wiktionary database dump..." % args.lang
    compressed_dump_path = "dumps/%swiktionary-latest-pages-articles.xml.bz2" % args.lang
    url = "https://dumps.wikimedia.org/%swiktionary/latest/%swiktionary-latest-pages-articles.xml.bz2" % (args.lang, args.lang)
    download_file(url, compressed_dump_path)
    print "Dump downloaded. Extracting..."
    with open(DUMP_FILE_PATH, 'wb') as dump_file, bz2.BZ2File(compressed_dump_path, 'rb') as dump_bz2:
        for data in iter(lambda: dump_bz2.read(100 * 1024), b''):
            dump_file.write(data)
    print "Dump extracted."

articles = dict()
count = 0

for event, element in etree.iterparse(DUMP_FILE_PATH, tag="{http://www.mediawiki.org/xml/export-0.10/}page"):
    title = element.findtext("{http://www.mediawiki.org/xml/export-0.10/}title")
    if (":" not in title and not (args.nonascii and is_ascii(title)) and element.find("{http://www.mediawiki.org/xml/export-0.10/}redirect") is None):
        revision = element.find("{http://www.mediawiki.org/xml/export-0.10/}revision")
        text = revision.findtext("{http://www.mediawiki.org/xml/export-0.10/}text")
        langsRE = re.compile(r'(^|\s)==.*[^=]==(\s|$)')
        langsMatch = langsRE.findall(text)
        articles[title] = len(langsMatch)
        count += 1
        if count % 10000 == 0:
            print '%d articles processed' % count
    element.clear()

Path("results").mkdir(exist_ok=True)
f = codecs.open("results/%s-topwords.txt" % args.lang, "w", "utf-8")
print "Writing results to file..."

count = 1
rank = count
prevRankVal = -1
for article in sorted(articles, key=articles.get, reverse=True):
    numLangs = articles[article]
    if numLangs != prevRankVal:
        rank = count
    prevRankVal = numLangs
    f.write("#%d\t%s: %d languages\n" % (rank, article, numLangs))
    count += 1
    if count > 10000:
        break
f.close()

print "Done."
