#!/usr/bin/env python

import re
import argparse
import operator
import datetime
from core.parsers.mention import Mention

def get_mentions(fname):
    """
    Extract 'NPRI in Print' or 'NPRI in the News' hits and return
    dicts of their metainfo.
    """
    capture = re.compile('NPRI in ?.* ?(news|print)', re.I)
    with open(fname) as fp:
        for line in fp:
            line = line.strip()
            if capture.search(line):
                yield get_info(line)

def get_info(hit):
    """
    Return a dict of info about the hit.
    """
    mention = Mention(hit)
    return dict(
        url = mention.info["url"],
        title = mention.info["title"],
        date = mention.info["datetime_date"] or datetime.date(1970, 1, 1),
        type = 'news' if mention.in_the_news else 'print',
        author = '(need author)',
        media = mention.info["media"],
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    args = parser.parse_args()

    mentions = get_mentions(args.input)
    outputs = []
    for mention in sorted(mentions, key=lambda e: e['date'], reverse=True):
        mention.update(dict(date = mention["date"].strftime("%B %e, %Y")))
        if mention['type'] == 'news':
            t = """<li><a href="%(url)s">%(title)s</a><br/><i>%(media)s</i>, %(date)s</li>"""
        elif mention['type'] == 'print':
            t = """<li><a href="%(url)s">%(title)s</a><br/>By %(author)s, <i>%(media)s</i>, %(date)s</li>"""
        output = t % mention
        outputs.append((mention['type'], output))

    with open('in-the-news/news.txt', 'w') as news, open('in-the-news/print.txt', 'w') as print_:
         for (mention, output) in outputs:
             output = output.encode('utf-8')
             if mention == 'news':
                 news.write(output + '\n')
             elif mention == 'print':
                 print_.write(output + '\n')

if __name__ == "__main__":
    main()
