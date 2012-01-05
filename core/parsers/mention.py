import httplib2
import datetime
from unipath import Path

from core.config import Config

class Mention(object):
    def __init__(self, line):
        self.line = line
        self.config = Config()
        if hasattr(self, 'url'):
            self.config_values = self.config.find_config_values(self.url)
        else:
            self.config_values = {}

    def date(self):
        return ""

    def medium(self):
        return ""

    def format(self):
        return ""

    def media(self):
        return ""

    def title(self):
        return ""

    def author(self):
        return ""

    def mentioned(self):
        return ""

    def topic(self):
        return ""

    def positive(self):
        return "Yes"

    def franklin(self):
        return "franklin" in self.line.lower()

    def duration(self):
        return

    def duplicate(self):
        return False

    def __str__(self):
        if hasattr(self, 'url'):
            return self.url
        else:
            return self.line.encode('utf-8')
