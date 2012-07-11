#!/usr/bin/env python

import re
import tablib
import datetime
import argparse

today = datetime.date.today().strftime("%Y%m%d")

parser = argparse.ArgumentParser()
parser.add_argument('input')
parser.add_argument('-o', '--output', default="%s-npri-in-print.txt" % today)
args = parser.parse_args()

tmpl = '<li><a href="%(url)s">%(title)s</a><br/>By %(author)s, <i>%(media)s</i>, %(date)s</li>\n'

media = {
    'rgj.com': 'Reno Gazette-Journal',
    'lvrj.com': 'Las Vegas Review-Journal',
    'lasvegassun.com': 'Las Vegas Sun',
    'elkodaily.com': 'Elko Daily Free Press',
    'nevadabusiness.com': 'Nevada Business',
    'nbj.com': 'Nevada Business',
}

output = open(args.output, 'w')

with open(args.input) as fp:
    data = tablib.Dataset()
    data.csv = fp.read()
    for row in data:
        date = datetime.datetime.strptime(row[0], "%m/%d/%Y")

        context = dict(
            date=date.strftime("%B %e, %Y"),
            media=row[1],
            title=row[2],
            author=row[3],
            url=row[4],
        )
        output.write((tmpl % context).encode('utf-8'))

output.close()
