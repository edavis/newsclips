#!/usr/bin/env python

from core.parsers import Article, Radio

HEADERS = "date medium format media title author mentioned "\
    "topic positive franklin duration url orig".split()

if __name__ == "__main__":
    import tablib
    import logging
    import collections
    from argparse import ArgumentParser, FileType

    parser = ArgumentParser()
    parser.add_argument('input', metavar='INPUT', type=open)
    parser.add_argument('-v', '--verbose', action="store_true", default=False)
    parser.add_argument('-q', '--quiet', action="store_true", default=False)
    parser.add_argument("-o", "--output", default="output.xlsx")
    parser.add_argument("-r", "--rejected", default="rejected.txt", type=FileType('w'))
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

    data = tablib.Dataset(headers=HEADERS)

    for line in args.input:
        item = collections.defaultdict(str)
        line = line.strip()

        if not line or line.startswith('----'):
            continue

        if line.startswith('#'):
            log.debug("Skipping %r" % line)
            args.rejected.write("%s\n" % line[1:])
            continue

        if line.startswith(('http://', 'https://')):
            # Penny Press NV publishes PDFs, so just create a dummy
            # object
            if 'pennypressnv.com' in line:
                class DummyMention(object):
                    def duplicate(self):
                        return False
                mention = DummyMention()
                mention.positive = 'Yes'
                mention.medium = 'Online'
                mention.format = 'Op-Ed'
                mention.media = 'Penny Press NV'
            else:
                mention = Article(line)
        else:
            mention = Radio(line)

        item["orig"] = line
        for key in HEADERS:
            try:
                func = getattr(mention, key)
                if func:
                    item[key] = func() if callable(func) else func
            except AttributeError:
                pass

        # clean-up as needed
        if item["franklin"]:
            item["franklin"] = 'Yes'
        else:
            item["franklin"] = ''

        if item["duration"]:
            item["duration"] = "%d minutes" % (item["duration"])
        else:
            item["duration"] = ''

        data.append([item[key] for key in HEADERS])

        if mention.duplicate():
            _item = item.copy()
            _item['orig'] = ''
            _item['url'] = ''
            if 'print' in mention.notes.lower():
                _item['medium'] = 'Print'
            elif 'tv' in mention.notes.lower():
                _item['medium'] = 'TV'
            elif 'radio' in mention.notes.lower():
                _item['medium'] = 'Radio'
                _item['format'] = 'Interview'
            data.append([_item[key] for key in HEADERS])

    with open(args.output, 'wb') as fp:
        fp.write(data.xlsx)
