import re
import urllib
import logging
import httplib2
import datetime
from unipath import Path
from lxml.html import document_fromstring
from dateutil.parser import parse as date_parse
from .mention import Mention

CACHE = Path("~/newsclips2/").expand()
CACHE.mkdir(parents=True)
HTTP = httplib2.Http(CACHE)

class Article(Mention):
    def __init__(self, line):
        self.log = logging.getLogger('newsclips2.article')
        self.url, self.notes = re.search(r'^(https?://[^ ]+) ?(.*)$', line).groups()
        self.tree = self.get_tree()
        super(Article, self).__init__(line)

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
                fp.write(self.content)

            return document_fromstring(self.content).xpath
        else:
            self.log.debug("  Using cache ('%s...')" % html_file.name[:60])
            with open(html_file) as fp:
                self.content = fp.read()
                return document_fromstring(self.content).xpath

    def date(self):
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
            return date.strftime("%m/%d/%Y")

        if not self.config_values:
            return ''

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
                self.log.error("  Couldn't date_parse %r, setting empty date" % value)
                date = ""

        if date:
            return date.strftime("%m/%d/%Y")
        else:
            return ""

    def medium(self):
        return u"Online"

    def format(self):
        return self.config_values.get("format", "")

    def media(self):
        return self.config_values.get("media", "")

    def title(self):
        return unicode(self.tree("//title/text()")[0].strip())

    def author(self):
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

        return ""

    def mentioned(self):
        staff = {}
        for k, v in self.config.config["staff"].items():
            staff[k] = v.split(', ')

        mentioned_staff = set()
        for employee, permutations in staff.iteritems():
            for name in permutations:
                name = name.encode('ascii')
                # remove newlines
                if name.lower() in " ".join(self.content.lower().split("\n")):
                    mentioned_staff.add(employee)

        return ", ".join(mentioned_staff)

    def positive(self):
        if 'neg' in self.notes.lower():
            return 'No'
        else:
            return 'Yes'

    def duplicate(self):
        """Return True if the mention should appear twice."""
        notes = self.notes.lower()
        return ('and online' in notes) or ('online and' in notes)
