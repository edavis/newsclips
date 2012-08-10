import re
import httplib2
from unipath import Path
from datetime import date
from collections import defaultdict

from ..config import Config
from article import Article
from radio import Radio
from core import HEADERS

class Mention(object):
    def __init__(self, line):
        self.info = defaultdict(str)
        self.line = line

        self.in_the_news = False
        self.duplicate = False

        if re.search('^https?://', line):
            obj = Article(line)
        else:
            obj = Radio(line)

        config = Config()
        obj.config_values = config[line]

        # we format here instead of in Article/Radio in case
        # we ever want/need to change the format
        if obj.date():
            self.info["date"] = obj.date().strftime("%m/%d/%Y")
            self.info["datetime_date"] = obj.date()
        else:
            self.info["date"] = ""

        self.info["medium"]    = obj.medium()
        self.info["format"]    = obj.format()
        self.info["media"]     = obj.media()
        self.info["title"]     = obj.title()
        self.info["author"]    = obj.author()
        self.info["mentioned"] = obj.mentioned()
        self.info["topic"]     = ""
        self.info["positive"]  = obj.positive()
        self.info["franklin"]  = obj.franklin()
        self.info["duration"]  = obj.duration()

        if isinstance(obj, Article):
            self.info["url"] = obj.url
            self.in_the_news = 'in the news' in line.lower()
            self.in_print = 'in print' in line.lower()
            self.duplicate = 'and online' in line.lower() #should this be for both Radio and Article?
        else:
            self.info["url"] = ""

        self.info["orig"] = line

    def append(self, data):
        """
        Given a `tablib.Dataset`, append this mention to it.

        Automatically handle print/online duplicates.
        """
        tags = ['in-the-news'] if self.in_the_news else []
        info = {key: self.info[key] for key in HEADERS}
        data.append([info[key] for key in HEADERS], tags=tags)

        if self.duplicate:
            info = info.copy()
            info["orig"] = ""
            info["url"] = ""

            if "print" in self.line.lower():
                info["medium"] = "Print"

            elif "tv" in self.line.lower():
                info["medium"] = "TV"

            elif 'radio' in self.line.lower():
                info["medium"] = "Radio"
                info["format"] = "Interview"

            data.append([info[key] for key in HEADERS])
