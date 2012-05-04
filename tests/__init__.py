import unittest2
from datetime import date
from core.parsers.mention import Mention
from core.config import Config
from core import HEADERS

class TestConfig(unittest2.TestCase):
    def setUp(self):
        self.config = Config("tests/test_config.ini")

    def test_sort_sections(self):
        self.assertEqual(list(self.config.sort_sections()), ["lvrj.com/blogs", "lvrj.com"])

    def test_domain_lookup(self):
        config = self.config["lvrj.com"]
        self.assertEqual(config, {"date": "today"})

        config = self.config["not here"]
        self.assertEqual(config, {})

class TestMention(unittest2.TestCase):
    def test_dates(self):
        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(mention.info["date"], "11/28/2011")

        mention = Mention("Andy on Alan Stock, 720 KDWN, 11/16/11, 60 minutes, Judicial conflict of interests, Foreclosure Mediation Program and Obamacare, Franklin story")
        self.assertEqual(mention.info["date"], "11/16/2011")

        # no date
        mention = Mention("Andy on Alan Stock, 720 KDWN, 60 minutes, Judicial conflict of interests, Foreclosure Mediation Program and Obamacare, Franklin story")
        self.assertEqual(mention.info["date"], "")

        # test 'today' dates
        mention = Mention("http://slashpolitics.reviewjournal.com/2012/03/depends-on-meaning-of-committed/")
        self.assertEqual(mention.info["date"], date.today().strftime("%m/%d/%Y"))

        # various date formats
        mention = Mention("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/")
        self.assertEqual(mention.info["date"], "11/19/2011")

        mention = Mention("http://www.rgj.com/article/20111130/NEWS19/111130028/Group-files-suit-challenging-ability-public-employees-serve-legislature")
        self.assertEqual(mention.info["date"], "11/30/2011")

        # date in html
        mention = Mention("http://www.lvrj.com/news/lawsuit-by-nevada-think-tank-targets-public-employees-serving-in-legislature-134770478.html")
        self.assertEqual(mention.info["date"], "11/30/2011")

        mention = Mention("http://nevadabusiness.com/issue/0112/38/2510")
        self.assertEqual(mention.info["date"], "")

        mention = Mention("Andy, 10 min. interview with 840 AM KXNT, 11/30/2011 on SOP lawsuit, interviewed by Samantha Stone")
        self.assertEqual(mention.info["date"], "11/30/2011")

    def test_medium(self):
        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(mention.info["medium"], "Online")

        mention = Mention("Andy on Alan Stock, 720 KDWN, 11/16/11, 60 minutes, Judicial conflict of interests, Foreclosure Mediation Program and Obamacare, Franklin story")
        self.assertEqual(mention.info["medium"], "Radio")

    def test_format(self):
        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(mention.info["format"], "Article")

        mention = Mention("Andy on Alan Stock, 720 KDWN, 11/16/11, 60 minutes, Judicial conflict of interests, Foreclosure Mediation Program and Obamacare, Franklin story")
        self.assertEqual(mention.info["format"], "Interview")

        mention = Mention("http://www.lvrj.com/opinion/nevada-not-a-low-tax-state-134553843.html?ref=843")
        self.assertEqual("Op-Ed", mention.info["format"])

    def test_media(self):
        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(mention.info["media"], "Las Vegas Business Press")

        mention = Mention("Andy on Alan Stock, 720 KDWN, 11/16/11, 60 minutes, Judicial conflict of interests, Foreclosure Mediation Program and Obamacare, Franklin story")
        self.assertEqual(mention.info["media"], "KDWN")

        mention = Mention("Andy, 10 min. interview with 840 AM KXNT, 11/30/11 on SOP lawsuit, interviewed by Samantha Stone")
        self.assertEqual(mention.info["media"], "KXNT")

        mention = Mention("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/")
        self.assertEqual("Las Vegas Sun", mention.info["media"])

    def test_title(self):
        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(mention.info["title"], "Las Vegas Business Press :: News : State employee pension plan funding ratio dips")

        mention = Mention("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/")
        self.assertTrue("Court wants nonprofit group to pay almost $1 million to review foreclosure records" in mention.info["title"])

    def test_author(self):
        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(mention.info["author"], "BY CHRIS SIEROTY")

        mention = Mention("http://www.lvrj.com/opinion/nevada-not-a-low-tax-state-134553843.html?ref=843")
        self.assertEqual("GEOFFREY LAWRENCE", mention.info["author"])

        # lvrj.com uses a different template when the op-ed is by us
        # vs. when the op-ed is written by a staffer
        mention = Mention("http://www.lvrj.com/opinion/coming-soon-pension-apocalypse-134553883.html")
        self.assertEqual("Glenn Cook", mention.info["author"])

        mention = Mention("http://www.lasvegasgleaner.com/las_vegas_gleaner/2011/12/unwitting-local-tools-of-corporate-overlords-hire-a-lawyer.html")
        self.assertEqual("Hugh Jackson", mention.info["author"])

    def test_mentioned(self):
        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(mention.info["mentioned"], "NPRI")

        mention = Mention("http://www.lasvegassun.com/news/2011/nov/30/conservative-group-sues-ban-public-employees-legis/")
        self.assertEqual("Andy Matthews, Joe Becker, NPRI", mention.info["mentioned"])

    def test_topic(self):
        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(mention.info["topic"], "")

    def test_positive(self):
        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(mention.info["positive"], "Yes")

        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt - neg")
        self.assertEqual(mention.info["positive"], "No")

    def test_franklin(self):
        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt - franklin")
        self.assertEqual(mention.info["franklin"], "Yes")

        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(mention.info["franklin"], "")

    def test_duration(self):
        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt - franklin")
        self.assertEqual(mention.info["duration"], "")

        mention = Mention("Andy on Alan Stock, 720 KDWN, 11/16/11, 60 minutes, Judicial conflict of interests, Foreclosure Mediation Program and Obamacare, Franklin story")
        self.assertEqual(mention.info["duration"], "60 minutes")

        mention = Mention("Andy, 10 min. interview with 840 AM KXNT, 11/30/11 on SOP lawsuit, interviewed by Samantha Stone")
        self.assertEqual(mention.info["duration"], "10 minutes")

        mention = Mention("Andy, interview with 840 AM KXNT, 11/30/11 on SOP lawsuit, interviewed by Samantha Stone")
        self.assertEqual(mention.info["duration"], "")

    def test_in_the_news(self):
        from tablib import Dataset, Databook
        data = Dataset()

        mention = Mention("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        mention.append(data)

        mention = Mention("http://www.lasvegasgleaner.com/las_vegas_gleaner/2011/12/unwitting-local-tools-of-corporate-overlords-hire-a-lawyer.html - NPRI in the News")
        mention.append(data)

        self.assertEqual(len(data), 2)
        self.assertEqual(len(data.filter(['in-the-news'])), 1)

    def test_dupe_entries(self):
        """
        Some stories need to be record twice: once the online version
        and again for the print version.
        """
