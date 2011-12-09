import csv
import logging

CSV_FIELD_NAMES = "date medium format media title author mentioned "\
    "topic positive franklin duration url notes".split()

class Writer(object):
    def __init__(self, output):
        self.output = output
        self.writer = csv.DictWriter(self.output, CSV_FIELD_NAMES,
                                     restval='EMPTY')
        self.log = logging.getLogger('newsclips2.writer')

    def add(self, mention):
        self.log.debug("Adding %r" % mention.line)

        if not mention.has_config:
            return self.writer.writerow({"url": str(mention)})

        values = dict(
            date      = mention.date().strftime("%Y-%m-%d"),
            medium    = mention.medium(),
            format    = mention.format(),
            media     = mention.media(),
            title     = mention.title().encode('utf-8'),
            author    = mention.author(),
            mentioned = ", ".join(mention.mentioned()),
            topic     = mention.topic(),
            positive  = "Yes" if mention.positive() else "No",
            franklin  = "Yes" if mention.franklin() else "",
            url       = str(mention))

        if mention.duration() is not None:
            values['duration'] = '%d minutes' % mention.duration()
        else:
            values['duration'] = ''

        if hasattr(mention, 'notes'):
            values["notes"] = mention.notes

        self.writer.writerow(values)

        if mention.duplicate():
            values = values.copy()
            values['url'] = ''
            values['medium'] = 'Print'
            values['notes'] = ''
            self.writer.writerow(values)
