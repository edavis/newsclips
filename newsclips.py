#!/usr/bin/env python

if __name__ == "__main__":
    import re
    import tablib
    import logging
    import datetime
    import collections
    from argparse import ArgumentParser, FileType

    from core import HEADERS
    from core.parsers.mention import Mention

    date_prefix = datetime.date.today().strftime("%Y%m%d")

    parser = ArgumentParser()
    parser.add_argument('input', metavar='INPUT', type=open)
    parser.add_argument("-o", "--output", default="%s-newsclips.xls" % date_prefix)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    log = logging.getLogger('newsclips.main')

    data = tablib.Dataset(headers=HEADERS)

    for line in args.input:
        item = {}
        line = line.strip()

        if not line:
            continue

        mention = Mention(line)
        mention.append(data)

    book = tablib.Databook((data, data.filter(["in-the-news"])))
    with open(args.output, 'wb') as fp:
        fp.write(book.xls)
