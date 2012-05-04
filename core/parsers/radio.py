import re
import logging
import datetime

class Radio(object):
    """
    Class to hold NPRI's radio appearances.
    """
    def __init__(self, line):
        self.line = line
        self.log = logging.getLogger('newsclips.radio')
        self.log.info(line)

    def date(self):
        match = re.search("(\d+)/(\d+)/(\d+)", self.line)
        if match:
            (month, day, year) = match.groups()
            if '20' in year:
                year = int(year)
            else:
                year = int('20' + year)
            return datetime.date(year, int(month), int(day))
        else:
            return

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
        elif 'steve' in self.line.lower():
            m.add('Steven Miller')
        elif 'geoff' in self.line.lower():
            m.add('Geoff Lawrence')
        elif 'victor' in self.line.lower():
            m.add('Victor Joecks')
        return ", ".join(m)

    def medium(self):
        return "Radio"

    def format(self):
        return "Interview"

    def media(self):
        match = re.search("([A-Z]{4})", self.line)
        if match:
            return unicode(match.group(1))

    def duration(self):
        match = re.search("(\d+) min", self.line)
        if match:
            minutes = int(match.group(1))
            return "%d minutes" % minutes
        else:
            return ""

    def positive(self):
        return 'Yes'

    def franklin(self):
        if 'franklin' in self.line.lower():
            return 'Yes'
        else:
            return ''
