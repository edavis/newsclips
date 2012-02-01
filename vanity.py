#!/usr/bin/env python

"""
vanity.py - format media hits for inclusion on npri.org

Input CSV file needs to have 4 columns:
- date (January 31, 2012 format)
- media
- title
- url

and ordered by `date DESC`
"""

import re
import tablib
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input", type=argparse.FileType('r'))
parser.add_argument("-o", "--output", default="output.txt", type=argparse.FileType('w'))
args = parser.parse_args()

data = tablib.Dataset()
data.csv = args.input.read()

html_string = """<li><a href="%(url)s">%(title)s</a>, <i>%(media)s</i>, %(date)s</li>\n"""

for row in data:
    (date, media, title, url) = row
    if ' - ' in title:
        title = re.search('^(?P<title>.+?) - ', title).group('title')
    elif ' | ' in title:
        title = re.search(r'^(?P<title>.+?) \| ', title).group('title')

    s = html_string % dict(date=date, media=media, title=title, url=url)
    args.output.write(s.encode('utf-8'))
