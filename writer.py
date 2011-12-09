import csv

CSV_FIELD_NAMES = "date medium format media title author mentioned "\
    "topic positive franklin duration url notes".split()

class Writer(object):
    def __init__(self, output):
        self.output = output
        self.writer = csv.DictWriter(self.output, CSV_FIELD_NAMES,
                                     restval='EMPTY')

    def add(self, mention):
        values = dict(
            date      = mention.date().strftime("%Y-%m-%d"),
            medium    = mention.medium(),
            format    = mention.format(),
            media     = mention.media(),
            title     = mention.title().encode('utf-8'),
            author    = mention.author(),
            mentioned = ", ".join(mention.mentioned()),
            topic     = "",
            positive  = "Yes" if mention.positive() else "No",
            franklin  = "Yes" if mention.franklin() else "No",
            url       = str(mention))

        if mention.duration() is not None:
            values['duration'] = '%d minutes' % mention.duration()
        else:
            values['duration'] = ''

        if hasattr(mention, 'notes'):
            values["notes"] = mention.notes

        self.writer.writerow(values)

        if mention.print_and_online():
            values = values.copy()
            values['url'] = ''
            values['medium'] = 'Print'
            values['notes'] = ''
            self.writer.writerow(values)
