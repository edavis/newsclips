import re
import logging
import datetime
from .mention import Mention

class Radio(Mention):
    """
    Class to hold NPRI's radio appearances.
    """
    def __init__(self, line):
        self.log = logging.getLogger('newsclips2.radio')
        self.log.info("Radio: '%s'" % line)
        super(Radio, self).__init__(line)

    def date(self):
        match = re.search("(\d+)/(\d+)/(\d+)", self.line)
        if match:
            (month, day, year) = match.groups()
            if '20' in year:
                year = int(year)
            else:
                year = int('20' + year)
            return datetime.date(year, int(month), int(day)).strftime("%m/%d/%Y")
        else:
            return ""

    def author(self):
        if 'alan' in self.line.lower():
            return 'Alan Stock'
        return ''

    def title(self):
        if 'alan' in self.line.lower():
            return 'The Alan Stock Show'

    def mentioned(self):
        m = set()
        if 'andy' in self.line.lower():
            m.add('Andy Matthews')
        elif re.search('steven?$', self.line.lower()):
            m.add('Steven Miller')
        elif 'geoff' in self.line.lower():
            m.add('Geoff Lawrence')
        elif 'victor' in self.line.lower():
            m.add('Victor Joecks')
        return ", ".join(m)

    def medium(self):
        return u"Radio"

    def format(self):
        return u"Interview"

    def media(self):
        match = re.search("([A-Z]{4})", self.line)
        if match:
            return unicode(match.group(1))

    def duration(self):
        match = re.search("(\d+) min", self.line)
        if match:
            return int(match.group(1))
