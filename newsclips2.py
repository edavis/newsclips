#!/usr/bin/env python

import re
import urllib
import logging
import httplib2
import datetime
from unipath import Path
from lxml.html import document_fromstring
from dateutil.parser import parse as date_parse

from config import Config

CACHE = Path("~/newsclips2/").expand()
CACHE.mkdir(parents=True)
HTTP = httplib2.Http(CACHE)

class Mention(object):
    def get_franklin_story(self):
        if hasattr(self, 'notes'):
            line = self.notes
        elif hasattr(self, 'line'):
            line = self.line
        return "franklin" in line.lower()
    franklin_story = property(get_franklin_story)

class Article(Mention):
    def __init__(self, line):
        self.line = line
        self.log = logging.getLogger('newsclips2.article')
        self.url, self.notes = re.search(r'^(https?://[^ ]+) ?(.*)$', line).groups()
        self.tree = self.get_tree()
        self.config = Config()
        self.config_values = self.config.find_config_values(self.url)
        self.has_config = "skip" not in self.config_values

        self.medium = u"Online"
        self.duration = u""

    def get_tree(self):
        """
        Return the DOM for the article content.

        Note this actually returns the XPATH method on the tree, so
        you can do: a.tree(<xpath>) directly.
        """
        quoted_url = urllib.quote(self.url, safe='')
        html_file = CACHE.child(quoted_url)
        self.log.info("URL: '%s'" % self.url)
        if not html_file.exists():
            self.log.debug("  Downloading")
            response, self.content = HTTP.request(self.url)
            status_code = int(response['status'])

            if not (200 <= status_code < 400):
                self.log.error("Got HTTP status code %d" % status_code)

            # cache content
            with open(html_file, 'w') as fp:
                fp.write(content)

            return document_fromstring(content).xpath
        else:
            self.log.debug("  Using cache ('%s...')" % html_file.name[:60])
            with open(html_file) as fp:
                self.content = fp.read()
                return document_fromstring(self.content).xpath

    def get_date(self):
        date = None

        # first check URL for common date patterns
        formats = [
            r"/(?P<year>20\d{2})[/-]?(?P<month>\d{1,2})[/-]?(?P<day>\d{1,2})?/",
            r"/(?P<month>\d{1,2})[/-]?(?P<day>\d{1,2})[/-]?(?P<year>20\d{2})/",
            r"/(?P<year>20\d{2})[/-]?(?P<month>[a-zA-z]{3})[/-]?(?P<day>\d{1,2})?/",
        ]

        for format in formats:
            match = re.search(format, self.url)
            if match:
                date_parts = match.groupdict()
                year = date_parts.get('year')
                month = date_parts.get('month')
                day = date_parts.get('day')

                if year and year.isdigit():
                    year = int(year)

                if month:
                    if month.isdigit():
                        month = int(month)
                    elif month.isalpha():
                        month = datetime.datetime.strptime(month, "%b").month

                if day and day.isdigit():
                    day = int(day)

                if all([year, month, day]):
                    date = datetime.date(year, month, day)

        # short-circuit if date was in the URL
        if date:
            return date

        xpath = self.config_values.get("date")
        date_re = self.config_values.get("date_re")

        if xpath == "today":
            return datetime.date.today()
        else:
            value = self.tree(xpath)
            value = " ".join(value).strip()
            if date_re is not None:
                match = re.search(date_re, value)
                if match:
                    value = match.group(1)
                else:
                    self.log.warn("  Supplied date_re but it didn't match")

            try:
                date = date_parse(value, fuzzy=True).date()
            except ValueError:
                self.log.error("  Couldn't date_parse %r, setting to 1/1/1970" % value)
                date = datetime.date(1970, 1, 1)

        return date

    def get_title(self):
        return unicode(self.tree("//title/text()")[0].strip())

    def get_author(self):
        author_xpaths = self.config_values.get("author").split("\n")
        author_re = self.config_values.get("author_re")

        for author_xpath in author_xpaths:
            if author_xpath.startswith("//"):
                value = self.tree(author_xpath)
                if value:
                    value = " ".join(value)
                    if author_re is not None:
                        match = re.search(author_re, value)
                        if match:
                            value = match.group(1)

                    return unicode(value.strip())
            else:
                return unicode(author_xpath)

    def get_format(self):
        return self.config_values["format"]

    def get_media(self):
        return self.config_values["media"]

    def get_positive(self):
        return 'neg' not in self.notes.lower()

    def get_mentioned(self):
        staff = {}
        for k, v in self.config.config["staff"].items():
            staff[k] = v.split(', ')

        mentioned_staff = set()
        for employee, permutations in staff.iteritems():
            for name in permutations:
                name = name.encode('ascii')
                if name.lower() in self.content.lower():
                    mentioned_staff.add(employee)

        return mentioned_staff

    date   = property(get_date)
    format = property(get_format)
    media  = property(get_media)
    title  = property(get_title)
    author = property(get_author)
    positive = property(get_positive)
    mentioned = property(get_mentioned)

class RadioAppearance(Mention):
    """
    Class to hold NPRI's radio appearances.
    """
    def __init__(self, line):
        self.line = line
        self.medium = u"Radio"
        self.format = u"Interview"
        self.title = u""
        self.author = u""
        self.positive = True
        self.mentioned = set()

        self.log = logging.getLogger('newsclips2.radio')
        self.log.info("Radio: '%s'" % self.line)

    def get_duration(self):
        match = re.search("(\d+) min", self.line)
        if match:
            return int(match.group(1))

    def get_date(self):
        match = re.search("(\d+)/(\d+)/(\d+)", self.line)
        if match:
            (month, day, year) = match.groups()
            return datetime.date(int('20' + year), int(month), int(day))

    def get_media(self):
        match = re.search("([A-Z]{4})", self.line)
        if match:
            return unicode(match.group(1))

    duration = property(get_duration)
    date = property(get_date)
    media = property(get_media)

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('input', metavar='INPUT', type=open)
    parser.add_argument('-v', '--verbose', action="store_true", default=False)
    parser.add_argument('-q', '--quiet', action="store_true", default=False)
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

    for line in args.input:
        line = line.strip()
        article = None

        if line.startswith('#'):
            log.debug("Skipping %r" % line)
            continue

        if line.startswith(('http://', 'https://')):
            mention = Article(line)
        else:
            mention = RadioAppearance(line)

        log.info("  Date      : %r" % mention.date)
        log.info("  Medium    : %r" % mention.medium)
        log.info("  Format    : %r" % mention.format)
        log.info("  Media     : %r" % mention.media)
        log.info("  Title     : %r" % mention.title)
        log.info("  Author    : %r" % mention.author)
        log.info("  Positive  : %r" % mention.positive)
        log.info("  Franklin  : %r" % mention.franklin_story)
        log.info("  Mentioned : %r" % mention.mentioned)
