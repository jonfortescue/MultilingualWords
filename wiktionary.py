import sys
import re
from lxml import etree
import codecs

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
        del uniconsole # reduce pollution, not needed anymore

# obtained from https://dumps.wikimedia.org/enwiktionary/
# provide a path via command line
DUMP_FILE_PATH = "dumps/%s" % sys.argv[1]

articles = dict()
count = 0

for event, element in etree.iterparse(DUMP_FILE_PATH, tag="{http://www.mediawiki.org/xml/export-0.10/}page"):
    title = element.findtext("{http://www.mediawiki.org/xml/export-0.10/}title")
    if (":" not in title and element.find("{http://www.mediawiki.org/xml/export-0.10/}redirect") is None):
        revision = element.find("{http://www.mediawiki.org/xml/export-0.10/}revision")
        text = revision.findtext("{http://www.mediawiki.org/xml/export-0.10/}text")
        langsRE = re.compile(r'(^|\s)==[^=]+==(\s|$)')
        langsMatch = langsRE.findall(text)
        articles[title] = len(langsMatch)
        count += 1
        if count % 10000 == 0:
            print '%d articles processed' % count
    element.clear()

f = codecs.open("topwords.txt", "w", "utf-8")
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
