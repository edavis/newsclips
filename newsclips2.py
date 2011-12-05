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
        self.config = ConfigParser(interpolation=ExtendedInterpolation())
        self.config.read([config])

    def __getitem__(self, domain):
        return dict(self.config.items(domain))

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
        if xpath is None:
            self.log.error("No date xpath given for '%s'" % self.url)

        date_index = self.config_values.get("date_index")
        if date_index is not None:
            date_index = int(date_index)

        date_prepare_func = self.config_values.get("date_prepare_func")
        if date_prepare_func is not None:
            date_prepare_func = eval(date_prepare_func)

        if xpath == "today":
            return datetime.date.today()
        else:
            value = self.tree(xpath)
            if isinstance(value, list):
                if len(value) == 1:
                    value = value[0].strip()
                elif date_index is not None:
                    value = value[date_index].strip()
                else:
                    value = " ".join(value).strip()

            if date_prepare_func is not None:
                value = date_prepare_func(value)

            date = date_parse(value, fuzzy=True).date()

        if date:
            return date
        else:
            return None

    def get_title(self):
        return unicode(self.tree("//title/text()")[0].strip())

    def get_author(self):
        author = self.config_values.get("author")
        author_index = self.config_values.get("author_index")
        if author_index is not None:
            author_index = int(author_index)

        if author.startswith("//"):
            value = self.tree(author)
            if isinstance(value, list):
                if author_index is not None:
                    value = value[author_index]
                else:
                    value = " ".join(value)
            return value.strip()
        else:
            return author

    date   = property(get_date)
    medium = property(lambda self: "Online")
    format = property(lambda self: self.config_values.get("format", ""))
    media  = property(lambda self: self.config_values.get("media", ""))
    title  = property(get_title)
    author = property(get_author)

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
        else:
            log.debug("Skipping '%s'" % line)

        if article:
            log.info("  Date   : %r" % article.date)
            log.info("  Medium : %r" % article.medium)
            log.info("  Format : %r" % article.format)
            log.info("  Media  : %r" % article.media)
            log.info("  Title  : %r" % article.title)
            log.info("  Author : %r" % article.author)
