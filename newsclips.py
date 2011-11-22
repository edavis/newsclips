#!/usr/bin/env python

import re
import sys
import json
import urllib
import hashlib
import logging
import httplib2
from lxml.html import document_fromstring
from datetime import date, datetime
from unipath import Path
from dateutil.parser import parse as date_parse

CACHE      = Path('~/newsclips/').expand()
HTTP_CACHE = CACHE.child('http')
HTML_CACHE = CACHE.child('html')

for directory in [HTTP_CACHE, HTML_CACHE]:
    directory.mkdir(parents=True)

http = httplib2.Http(HTTP_CACHE)

class Article(object):
    def __init__(self, line, csv):
        self.url, self.notes = re.search(r'^(https?://[^ ]+) ?(.*)$', line).groups()
        self.csv = csv
        self.log = logging.getLogger('npri.newsclips.article')

        self.download_article()
        self.write_csv()

    def download_article(self):
        quoted_url = urllib.quote(self.url, safe='')
        html_file = HTML_CACHE.child(quoted_url + '.html')
        response_file = HTML_CACHE.child(quoted_url + '.json')

        if not html_file.exists() or not response_file.exists():
            self.log.info("Downloading '%s'" % self.url)
            self.response, self.content = http.request(self.url)

            status_code = int(self.response['status'])

            if not (200 <= status_code < 400):
                self.log.warning("Got HTTP status code %d" % status_code)

            with open(html_file, 'w') as fp:
                fp.write(self.content)

            with open(response_file, 'w') as fp:
                json.dump(self.response, fp)
        else:
            self.log.debug("Opening '%s'" % self.url)

            with open(html_file) as fp:
                self.content = fp.read()

            with open(response_file) as fp:
                self.response = json.load(fp)

        self.tree = document_fromstring(self.content)


    @property
    def date(self):
        date_obj = None

        if 'nevadabusiness.com' in self.url:
            date_obj = date.today()

        # Need to catch '/blogs/sherm' here or the 'lvrj.com' rule below will
        elif 'lvrj.com/blogs/sherm' in self.url:
            date_string = self.tree.xpath("//span[@class='post_timestamp']/text()")[0].strip()
            date_obj = datetime.strptime(date_string, "%A, %b. %d, %Y at %I:%M %p").date()

        elif 'lvrj.com' in self.url:
            date_string = self.tree.xpath("//div[@id='updated']/text()")[0].strip()
            date_string, time_string = date_string.split('|', 1)
            date_string = date_string.strip()
            date_obj = datetime.strptime(date_string, "Posted: %b. %d, %Y").date()

        elif 'fernleynews.ning.com' in self.url:
            date_string = self.tree.xpath("//ul[@class='navigation byline']/li[1]/a[3]/text()")[0].strip()
            date_string, time_string = date_string.split('at', 1)
            date_string = date_string.strip()
            date_obj = datetime.strptime(date_string, "on %B %d, %Y").date()

        elif 'smartmoney.com' in self.url:
            date_string = self.tree.xpath("//li[@class='dateStamp']/small/text()")[0].strip()
            bits = date_string.split(', ')
            date_string = " ".join((bits[0], bits[1]))
            date_obj = datetime.strptime(date_string, "%B %d %Y")

        elif 'lvtsg.com' in self.url:
            month = self.tree.xpath("//div[@class='date']/span[@class='month']/text()")[0].strip()
            day = self.tree.xpath("//div[@class='date']/span[@class='day']/text()")[0].strip()
            year = self.tree.xpath("//div[@class='date']/span[@class='year']/text()")[0].strip()
            date_obj = datetime.strptime(" ".join([month, day, year]), "%b %d %Y")

        elif 'laketahoenews.net' in self.url:
            date_string = self.tree.xpath("//div[@class='post-info']/text()")[-1]
            date_obj = date_parse(date_string, fuzzy=True).date()

        # For some reason the dates in the URLs aren't showing up anymore
        elif 'nevadanewsandviews.com/archives' in self.url:
            date_string = self.tree.xpath("//div[@id='entryMeta']/p/text()")[1]
            date_obj = date_parse(date_string, fuzzy=True).date()

        elif 'lasvegastribune.com' in self.url:
            date_string = self.tree.xpath("//span[@class='createdate']/text()")[0]
            date_obj = date_parse(date_string, fuzzy=True).date()

        elif 'ediswatching.org' in self.url:
            date_string = " ".join(self.tree.xpath("//div[@class='date']/div/text()"))
            date_obj = date_parse(date_string, fuzzy=True).date()

        xpaths = {
            'crankyhermit.blogspot.com'              : ("//h2[@class='date-header']/span/text()", "%A, %B %d, %Y"),
            'newsreview.com'                         : ("//div[@style='font-size:10px;']/a/text()", "%m.%d.%y"),
            'elkodaily.com'                          : ("//span[@class='updated']/@title", "%Y-%m-%dT%H:%M:%SZ"),
            'thisisreno.com'                         : ("//div[@class='date']/text()", "%B %d, %Y"),
            'thenevadaview.com'                      : ("//p[@class='post-details']/text()", "Posted on %d. %b, %Y by"),
            'conpats.blogspot.com'                   : ("//h2[@class='date-header']/span/text()", "%A, %B %d, %Y"),
            'blog.mises.org'                         : ("//abbr[@class='published']/@title", "%Y-%m-%d"),
            'online.wsj.com'                         : ("//li[@class='dateStamp']/small/text()", "%B %d, %Y"),
            'leonardfoster.com/blog'                 : ("//time[@class='entry-date']/@datetime", "%Y-%m-%dT%H:%M:%S+00:00"),
            'examiner.com/conservative-in-las-vegas' : ("//span[@class='date']/@content", "%Y-%m-%dT%H:%M:%S-07:00"),
            'lasvegasbadger.blogspot.com'            : ("//h2[@class='date-header']/span/text()", "%A, %B %d, %Y"),
            'deseretnews.com'                        : ("//div[@class='story-content']//div[@class='timestamp']/text()", date_parse),
        }

        for domain, (xpath, date_format) in xpaths.iteritems():
            if domain in self.url:
                try:
                    s = self.tree.xpath(xpath)[0].strip()
                    if callable(date_format):
                        date_obj = date_format(s, fuzzy=True).date()
                    else:
                        date_obj = datetime.strptime(s, date_format).date()
                except IndexError:
                    self.log.exception("Found matching domain (%s) for 'date', but the xpath didn't work" % domain)
                    raise SystemExit

        # Suss out the date from the URL
        date_formats = [
            r"/(?P<year>20\d{2})[/-]?(?P<month>\d{1,2})[/-]?(?P<day>\d{1,2})?/",
            r"/(?P<month>\d{1,2})[/-]?(?P<day>\d{1,2})[/-]?(?P<year>20\d{2})/",
            r"/(?P<year>20\d{2})[/-]?(?P<month>[a-zA-z]{3})[/-]?(?P<day>\d{1,2})?/",
        ]

        for fmt in date_formats:
            match = re.search(fmt, self.url, re.VERBOSE)
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
                        month = datetime.strptime(month, "%b").month

                if day and day.isdigit():
                    day = int(day)

                if all([year, month, day]):
                    date_obj = date(year, month, day)

        return date_obj.strftime("%m/%d/%Y") if date_obj else ""


    @property
    def format(self):
        if "tahoebonanza.com" in self.url and "Jim Clark" in self.title:
            return "Op-Ed"

        elif "lvrj.com/opinion" in self.url:
            return "Op-Ed"

        # special case for washingtontimes.com
        if "washingtontimes.com" in self.url:
            if '''var zone="opinion_commentary"''' in self.content:
                return "Op-Ed"

        formats = {
            "Blog": [
                "nevadanewsandviews.com",
                "crankyhermit.blogspot.com",
                "nvemployees.wordpress.com",
                "muthstruths.com",
                "newsreview.com",
                "desertbeacon.wordpress.com",
                "thenevadaview.com",
                "conpats.blogspot.com",
                "blog.mises.org",
                "4thst8.wordpress.com",
                "blog.heritage.org",
                "detnews.com",
                "smartmoney.com",
                "lvtsg.com",
                "washoecountygop.org",
                "leonardfoster.com/blog",
                "lasvegasbadger.blogspot.com",
                "beyondbenevolence.wordpress.com",
                "ediswatching.org",
                ],

            "Article": [
                "lvrj.com",
                "lasvegassun.com",
                "nevadanewsbureau.com",
                "elkodaily.com",
                "lvbusinesspress.com",
                "fernleynews.ning.com",
                "thisisreno.com",
                "elynews.com",
                "lasvegasweekly.com",
                "news.heartland.org",
                "online.wsj.com",
                "examiner.com",
                "deseretnews.com",
                "laketahoenews.net",
                "nevadaappeal.com",
                "lasvegastribune.com",
                ],

            "Op-Ed": [
                "nevadabusiness.com",
                ],
        }

        for fmt, domains in formats.iteritems():
            for domain in domains:
                if domain in self.url:
                    return fmt

        return ""


    @property
    def media(self):
        media = {
            "conpats.blogspot.com"            : "Conservative Patriot",
            "crankyhermit.blogspot.com"       : "Cranky Hermit",
            "desertbeacon.wordpress.com"      : "Desert Beacon",
            "elkodaily.com"                   : "Elko Daily",
            "fernleynews.ning.com"            : "Fernley News",
            "lasvegassun.com"                 : "Las Vegas Sun",
            "lvbusinesspress.com"             : "Las Vegas Business Press",
            "lvrj.com"                        : "Las Vegas Review-Journal",
            "muthstruths.com"                 : "Muth's Truths",
            "nevadabusiness.com"              : "Nevada Business",
            "nevadanewsandviews.com"          : "Nevada News and Views",
            "nevadanewsbureau.com"            : "Nevada News Bureau",
            "newsreview.com"                  : "Reno News & Review",
            "nvemployees.wordpress.com"       : "Nevada State Employee Focus",
            "tahoebonanza.com"                : "Tahoe Bonanza",
            "thenevadaview.com"               : "The Nevada View",
            "thisisreno.com"                  : "This Is Reno",
            "blog.mises.org"                  : "Mises Economics Blog",
            "4thst8.wordpress.com"            : "4th St8 (Fourth Estate)",
            "blog.heritage.org"               : "The Foundry (Heritage Blog)",
            "elynews.com"                     : "Ely News",
            "detnews.com"                     : "The Michigan View",
            "smartmoney.com"                  : "Smart Money",
            "washingtontimes.com"             : "The Washington Times",
            "lvtsg.com"                       : "Las Vegas TSG Business News",
            "lasvegasweekly.com"              : "Las Vegas Weekly",
            "news.heartland.org"              : "Heartland News",
            "washoecountygop.org"             : "Washoe County GOP",
            "online.wsj.com"                  : "Wall Street Journal",
            "leonardfoster.com/blog"          : "Leonard Foster's Blog",
            "examiner.com"                    : "Examiner.com",
            "lasvegasbadger.blogspot.com"     : "Las Vegas Badger",
            "beyondbenevolence.wordpress.com" : "The Sandbar Group",
            "deseretnews.com"                 : "Deseret News",
            "laketahoenews.net"               : "Lake Tahoe News",
            "nevadaappeal.com"                : "Nevada Appeal",
            "lasvegastribune.com"             : "Las Vegas Tribune",
            "ediswatching.org"                : "Ed is Watching",
        }

        for domain, media_title in media.iteritems():
            if domain in self.url:
                return media_title

        return ""


    @property
    def title(self):
        return unicode(self.tree.xpath("//head/title/text()")[0].strip())


    @property
    def author(self):
        # Single author blogs
        if 'nvemployees.wordpress.com' in self.url:
            return "Jim Pierce"

        elif 'muthstruths.com' in self.url:
            return "Chuck Muth"

        elif 'desertbeacon.wordpress.com' in self.url:
            return "Desert Beacon"

        elif "4thst8.wordpress.com" in self.url:
            return "Thomas Mitchell"

        elif 'lvrj.com/blogs/sherm' in self.url:
            return "Sherm Frederick"

        # The LVRJ op-ed section uses a different template than the regular
        # news section, so we have to do it like this.
        #
        # /opinion/ must come before lvrj.com proper
        elif 'lvrj.com/opinion' in self.url:
            xpaths = [
                "//div[@id='columnist']/h2/text()",
                "//div[@id='byline']/text()",
            ]
            for xpath in xpaths:
                try:
                    return self.tree.xpath(xpath)[0].strip()
                except IndexError:
                    continue

            if self.tree.xpath("//h2[@class='kicker']"):
                return "LVRJ Editorial Staff"

        elif 'lvrj.com' in self.url:
            return self.tree.xpath("//div[@id='byline']/a/text()")[0].strip()

        elif 'lasvegassun.com/blogs/ralstons-flash' in self.url:
            return "Jon Ralston"

        elif "beyondbenevolence.wordpress.com" in self.url:
            return "The Sandbar Group"

        elif "laketahoenews.net" in self.url:
            return "Staff"

        elif "ediswatching.org" in self.url:
            return "Jon Caldara"

        xpaths = {
            'nevadanewsandviews.com'      : "//a[@rel='author']/text()",
            'nevadabusiness.com'          : "//p[@class='articleAuthor']/text()",
            'crankyhermit.blogspot.com'   : "//span[@class='fn']/text()",
            'tahoebonanza.com'            : "//div[@class='byline']/text()",
            'nevadanewsbureau.com'        : "//a[@class='author-link']/text()",
            'lasvegassun.com'             : "//p[@class='byline']/a/cite/text()",
            'newsreview.com'              : "//meta[@name='Author']/@content",
            'lvbusinesspress.com'         : "//span[@class='byline']/text()",
            'elkodaily.com'               : "//span[@class='fn']/text()",
            'fernleynews.ning.com'        : "//ul[@class='navigation byline']/li[1]/a[2]/text()",
            'thisisreno.com'              : "//div[@class='entry']/p[1]/text()",
            'thenevadaview.com'           : "//a[@rel='author']/text()",
            'conpats.blogspot.com'        : "//span[@class='fn']/text()",
            'blog.mises.org'              : "//a[@rel='author']/text()",
            'blog.heritage.org'           : "//p[@class='author']/a[1]/text()",
            'elynews.com'                 : "//div[@id='story']/h5/text()",
            'detnews.com'                 : "//div[@id='articleBody']/h4/text()",
            'smartmoney.com'              : "//h3[@class='byline']/a/text()",
            'washingtontimes.com'         : "//span[@class='fn']/text()",
            'lvtsg.com'                   : "//span[@class='author']/a/text()",
            'lasvegasweekly.com'          : "//p[@class='article_wide_author']/a/text()",
            'news.heartland.org'          : "//h4[@class='title small-title']/a/text()",
            'washoecountygop.org'         : "//a[@rel='author']/text()",
            'online.wsj.com'              : "//h3[@class='byline']/a/text()",
            'leonardfoster.com/blog'      : "//a[@rel='author']/text()",
            'examiner.com'                : "//a[@rel='author']/text()",
            'lasvegasbadger.blogspot.com' : "//span[@class='post-author vcard']/span[@class='fn']/text()",
            'deseretnews.com'             : "//p[@class='author-text']/text()",
            'nevadaappeal.com'            : "//div[@class='byline']/a/text()",
            'lasvegastribune.com'         : "//span[@class='createdby']/text()",
        }

        for domain, xpath in xpaths.iteritems():
            if domain in self.url:
                try:
                    s = self.tree.xpath(xpath)[0].strip()

                    if '\n' in s:
                        return " ".join(s.split('\n'))

                    return s

                except IndexError:
                    self.log.debug("xpath = %r" % xpath)
                    self.log.debug("tree = %r" % self.tree.xpath(xpath))
                    self.log.exception("Found matching domain (%s) for 'author', but the xpath didn't work" % domain)
                    raise SystemExit

        return ""


    @property
    def mentioned(self):
        staff_members = {
            "Alexander Cooper"  : ["Alex Cooper", "Alexander Cooper"],
            "Andy Matthews"     : ["Andy Matthews", "Andrew Matthews"],
            "Eric Davis"        : ["Eric Davis"],
            "Geoffrey Lawrence" : ["Geoff Lawrence", "Geoffrey Lawrence"],
            "Karen Gray"        : ["Karen Gray"],
            "Kyle Gillis"       : ["Kyle Gillis"],
            "NPRI"              : ["NPRI", "Nevada Policy Research Institute",
                                   "Write on Nevada", "writeonnevada.com"],
            "Sharon Rossie"     : ["Sharon Rossie"],
            "Steve Miller"      : ["Steven Miller", "Steve Miller"],
            "TransparentNevada" : ["TransparentNevada", "Transparent Nevada"],
            "Victor Joecks"     : ["Victor Joecks"],
        }
        mentioned = set()

        for proper_name, possible_names in staff_members.iteritems():
            for name in possible_names:
                if name.lower() in self.content.lower():
                    mentioned.add(proper_name)

        return ", ".join(sorted(mentioned)) if mentioned else ""


    @property
    def positive(self):
        return "No" if "neg" in self.notes else "Yes"

    def write_csv(self):
        fieldnames = "date medium format "\
            "media title author "\
            "mentioned topic positive "\
            "duration url notes".split()

        row = {
            "date"      : self.date,
            "medium"    : "Online",
            "format"    : self.format,
            "media"     : self.media,
            "title"     : self.title,
            "author"    : self.author,
            "mentioned" : self.mentioned,
            "topic"     : "",
            "positive"  : self.positive,
            "duration"  : "",
            "url"       : self.url,
            "notes"     : self.notes,
        }

        self.csv.writerow([row[k] for k in fieldnames])

        if 'print' in self.notes:
            row["medium"] = "Print"
            row["url"] = ""
            row["notes"] = ""
            self.csv.writerow([row[k] for k in fieldnames])

if __name__ == "__main__":
    import argparse
    import unicodecsv

    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=open)
    parser.add_argument("-o", "--output", default="output.csv")
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    args = parser.parse_args()

    logging.basicConfig(
        level = logging.DEBUG if args.debug else logging.INFO,
        datefmt = "%D %r",
        format = "%(asctime)s %(levelname)s: %(message)s",
    )

    log = logging.getLogger('npri.newsclips.main')

    csv = unicodecsv.writer(open(args.output, 'w'))

    log.debug("Opening email file %s" % args.input.name)

    count = 0
    for line in args.input:
        line = line.strip()

        if not line:
            continue

        if not line.startswith('http://'):
            log.debug("Skipping '%s'" % line)
            continue

        Article(line, csv)
        count += 1

    log.info("Parsed %d urls into %s" % (count, args.output))
