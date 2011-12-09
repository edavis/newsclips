#!/usr/bin/env python

from config import Config
from article import Article
from radio import Radio
from writer import Writer

if __name__ == "__main__":
    import os
    import logging
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('input', metavar='INPUT', type=open)
    parser.add_argument('-v', '--verbose', action="store_true", default=False)
    parser.add_argument('-q', '--quiet', action="store_true", default=False)
    parser.add_argument("-o", "--output", default="output.csv")
    args = parser.parse_args()

    if args.verbose:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.CRITICAL
    else:
        level = logging.INFO

    logging.basicConfig(
        datefmt="%r",
        format="%(levelname)-5s: %(message)s",
        level=level)

    log = logging.getLogger('newsclips2.main')

    mentions = []

    for line in args.input:
        line = line.strip()

        if line.startswith(('#', '----')):
            log.debug("Skipping %r" % line)
            continue

        if line.startswith(('http://', 'https://')):
            mention = Article(line)
        else:
            mention = Radio(line)

        mentions.append(mention)

    with open(args.output, 'w') as fp:
        writer = Writer(fp)
        for mention in mentions:
            writer.add(mention)

    os.system("gnumeric '%s'&" % args.output)
