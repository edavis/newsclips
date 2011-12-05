#!/usr/bin/env python

import re
import urllib
import logging
import httplib2
import datetime
from unipath import Path
from lxml.html import document_fromstring
from configparser import ConfigParser, ExtendedInterpolation
from dateutil.parser import parse as date_parse

CACHE = Path("~/newsclips2/").expand()
CACHE.mkdir(parents=True)
HTTP = httplib2.Http(CACHE)

class Config(object):
    def __init__(self, config="config.ini"):
        self.config = ConfigParser(interpolation=ExtendedInterpolation(),
                                   allow_no_value=True)
        self.config.read([config])
        self.log = logging.getLogger('newsclips2.config')

    def __getitem__(self, domain):
        self.log.debug("  Getting config values for '%s'" % domain)
        values = dict(author='', medium='', media='', format='')
        values.update(dict(self.config.items(domain)))
        return values

    def sort_sections(self):
        """
        Yield section names in `len` descending order.
        """
        # longer sections should appear first because they'll be more
        # "unique."
        #
        # For example: If the URL is "lvrj.com/blogs/sherm" and the config
        # file contains both "lvrj.com/blogs/sherm" and "lvrj.com," we want
        # it to match with "lvrj.com/blogs/sherm" instead of just "lvrj.com."
        for section in sorted(self.config.sections(), key=len, reverse=True):
            yield section

    def find_config_values(self, url):
        """
        Given a URL, return its "xpath info" for how to parse.
        """
        for section in self.sort_sections():
            if section in url:
                return self[section]

class Article(object):
    def __init__(self, line):
        self.line = line
        self.log = logging.getLogger('newsclips2.article')
        self.url, self.notes = re.search(r'^(https?://[^ ]+) ?(.*)$', line).groups()
        self.tree = self.get_tree()
        self.config = Config()
        self.config_values = self.config.find_config_values(self.url)
        self.has_config = "skip" not in self.config_values
        self.medium = u"Online"

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
            response, content = HTTP.request(self.url)
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
                return document_fromstring(fp.read()).xpath

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

    def get_franklin_story(self):
        return 'franklin' in self.notes.lower()

    date   = property(get_date)
    format = property(get_format)
    media  = property(get_media)
    title  = property(get_title)
    author = property(get_author)
    positive = property(get_positive)
    franklin_story = property(get_franklin_story)

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

        if line.startswith(('http://', 'https://')):
            article = Article(line)
            if article.has_config:
                log.info("  Date   : %r" % article.date)
                log.info("  Medium : %r" % article.medium)
                log.info("  Format : %r" % article.format)
                log.info("  Media  : %r" % article.media)
                log.info("  Title  : %r" % article.title)
                log.info("  Author : %r" % article.author)
            else:
                log.info("  Section said to skip")
        else:
            log.debug("Skipping '%s'" % line)


