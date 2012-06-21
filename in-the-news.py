#!/usr/bin/env python

import time
import tablib
import argparse
from datetime import date

parser = argparse.ArgumentParser()
parser.add_argument('input')
parser.add_argument('-o', '--output', default="output.txt")
args = parser.parse_args()

media_hits = tablib.Dataset()
with open(args.input) as fp:
    media_hits.csv = fp.read()

hits = []
last_url = None
for row in media_hits:
    medium = row[1]
    hit_format = row[2]
    if row[11]:
        last_url = row[11]

    if medium == 'Print' and hit_format == 'Article':
        title = row[4]
        media = row[3]
        date = row[0]

        hits.append(dict(
            title=title, url=last_url,
            media=media, date=date))

tmpl = '<li><a href="%(url)s">%(title)s</a><br/><i>%(media)s</i>, %(date)s</li>\n'

with open(args.output, 'w') as fp:
    for hit in reversed(hits):
        hit['date'] = time.strptime(hit["date"], "%m/%d/%Y")
        hit["date"] = time.strftime("%B %e, %Y", hit["date"])
        fp.write((tmpl % hit).encode('utf-8'))
