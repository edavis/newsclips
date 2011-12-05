import unittest2
from datetime import date
from newsclips2 import Article, Config

class TestConfig(unittest2.TestCase):
    def test_find_config_values(self):
        config = Config("test_config.ini")
        self.assertEqual(list(config.sort_sections()), ["lvrj.com/blogs", "lvrj.com"])

class TestArticle(unittest2.TestCase):
    def test_get_date_by_url(self):
        a = Article("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(a.date, date(2011, 11, 28))

        a = Article("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/")
        self.assertEqual(a.date, date(2011, 11, 19))

        a = Article("http://www.rgj.com/article/20111130/NEWS19/111130028/Group-files-suit-challenging-ability-public-employees-serve-legislature")
        self.assertEqual(a.date, date(2011, 11, 30))

        a = Article("http://www.lvrj.com/news/lawsuit-by-nevada-think-tank-targets-public-employees-serving-in-legislature-134770478.html")
        self.assertEqual(a.date, date(2011, 11, 30))

    def test_get_title(self):
        a = Article("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/")
        self.assertTrue(u"Court wants nonprofit group to pay almost $1 million to review foreclosure records" in a.title)

    def test_get_author(self):
        a = Article("http://www.lvrj.com/opinion/nevada-not-a-low-tax-state-134553843.html?ref=843")
        self.assertEqual("GEOFFREY LAWRENCE", a.author)
