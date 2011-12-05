import unittest2
from datetime import date
from newsclips2 import Article, RadioAppearance, Config

class TestConfig(unittest2.TestCase):
    def test_find_config_values(self):
        config = Config("test_config.ini")
        self.assertEqual(list(config.sort_sections()), ["lvrj.com/blogs", "lvrj.com"])

class TestRadioAppearance(unittest2.TestCase):
    def test_get_duration(self):
        r = RadioAppearance("Andy on Alan Stock, 720 KDWN, 11/16/11, 60 minutes, Judicial conflict of interests, Foreclosure Mediation Program and Obamacare, Franklin story")
        self.assertEqual(r.duration, 60)

        r = RadioAppearance("Andy, 10 min. interview with 840 AM KXNT, 11/30/11 on SOP lawsuit, interviewed by Samantha Stone")
        self.assertEqual(r.duration, 10)

    def test_get_date(self):
        r = RadioAppearance("Andy on Alan Stock, 720 KDWN, 11/16/11, 60 minutes, Judicial conflict of interests, Foreclosure Mediation Program and Obamacare, Franklin story")
        self.assertEqual(r.date, date(2011, 11, 16))

        r = RadioAppearance("Andy, 10 min. interview with 840 AM KXNT, 11/30/11 on SOP lawsuit, interviewed by Samantha Stone")
        self.assertEqual(r.date, date(2011, 11, 30))

    def test_get_media(self):
        r = RadioAppearance("Andy on Alan Stock, 720 KDWN, 11/16/11, 60 minutes, Judicial conflict of interests, Foreclosure Mediation Program and Obamacare, Franklin story")
        self.assertEqual(r.media, "KDWN")

        r = RadioAppearance("Andy, 10 min. interview with 840 AM KXNT, 11/30/11 on SOP lawsuit, interviewed by Samantha Stone")
        self.assertEqual(r.media, "KXNT")

    def test_get_franklin_story(self):
        r = RadioAppearance("Andy, 10 min. interview with 840 AM KXNT, 11/30/11 on SOP lawsuit, interviewed by Samantha Stone, Franklin story")
        self.assertTrue(r.franklin_story)

        r = RadioAppearance("Andy, 10 min. interview with 840 AM KXNT, 11/30/11 on SOP lawsuit, interviewed by Samantha Stone")
        self.assertFalse(r.franklin_story)

class TestArticle(unittest2.TestCase):
    def test_get_date(self):
        a = Article("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(date(2011, 11, 28), a.date)

        a = Article("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/")
        self.assertEqual(date(2011, 11, 19), a.date)

        a = Article("http://www.rgj.com/article/20111130/NEWS19/111130028/Group-files-suit-challenging-ability-public-employees-serve-legislature")
        self.assertEqual(date(2011, 11, 30), a.date)

        a = Article("http://www.lvrj.com/news/lawsuit-by-nevada-think-tank-targets-public-employees-serving-in-legislature-134770478.html")
        self.assertEqual(date(2011, 11, 30), a.date)

        a = Article("http://nevadabusinesscoalition.com/?p=1682")
        self.assertEqual(date.today(), a.date)

    def test_get_title(self):
        a = Article("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/")
        self.assertTrue(u"Court wants nonprofit group to pay almost $1 million to review foreclosure records" in a.title)

    def test_get_author(self):
        a = Article("http://www.lvrj.com/opinion/nevada-not-a-low-tax-state-134553843.html?ref=843")
        self.assertEqual("GEOFFREY LAWRENCE", a.author)

        # lvrj.com uses a different template when the op-ed is by us
        # vs. when the op-ed is written by a staffer
        a = Article("http://www.lvrj.com/opinion/coming-soon-pension-apocalypse-134553883.html")
        self.assertEqual("Glenn Cook", a.author)

        a = Article("http://www.lasvegasgleaner.com/las_vegas_gleaner/2011/12/unwitting-local-tools-of-corporate-overlords-hire-a-lawyer.html")
        self.assertEqual("Hugh Jackson", a.author)

        a = Article("http://nevadabusinesscoalition.com/?p=1682")
        self.assertEqual("Mike Chamberlain", a.author)

    def test_get_format(self):
        a = Article("http://www.lvrj.com/opinion/nevada-not-a-low-tax-state-134553843.html?ref=843")
        self.assertEqual("Op-Ed", a.format)

    def test_get_media(self):
        a = Article("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/")
        self.assertEqual("Las Vegas Sun", a.media)

    def test_get_medium(self):
        a = Article("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/")
        self.assertEqual("Online", a.medium)

    def test_get_positive(self):
        a = Article("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/")
        self.assertTrue(a.positive)

        a = Article("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/ - neg")
        self.assertFalse(a.positive)

    def test_get_franklin_story(self):
        a = Article("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/ - print and online, Franklin story")
        self.assertTrue(a.franklin_story)

        a = Article("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/ - print and online")
        self.assertFalse(a.franklin_story)

    def test_get_mentioned(self):
        a = Article("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/ - print and online")
        self.assertTrue("NPRI" in a.mentioned)

        a = Article("http://www.lasvegassun.com/news/2011/nov/30/conservative-group-sues-ban-public-employees-legis/")
        self.assertEqual(set(["Andy Matthews", "NPRI", "Joe Becker"]), a.mentioned)
