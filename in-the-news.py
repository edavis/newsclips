#!/usr/bin/env python

import re
import datetime
import argparse

today = datetime.date.today().strftime("%Y%m%d")

parser = argparse.ArgumentParser()
parser.add_argument('input')
parser.add_argument('-o', '--output', default="%s-in-the-news.txt" % today)
args = parser.parse_args()

tmpl = '<li><a href="%(url)s">(no title)</a><br/><i>%(media)s</i>, (no date)</li>\n'

media = {
    'rgj.com': 'Reno Gazette-Journal',
    'lvrj.com': 'Las Vegas Review-Journal',
    'lasvegassun.com': 'Las Vegas Sun',
}

output = open(args.output, 'w')

with open(args.input) as fp:
    for line in fp:
        line = line.strip()

        if 'in the news' in line.lower():
            url = re.search(r'^([^ ]+)', line).group(1)
            context = {'url': url, 'media': '(no media)'}

            for media_url, media_name in media.iteritems():
                if media_url in url:
                    context['media'] = media_name
                    break

            output.write(tmpl % context)

output.close()
