import unittest2
from datetime import date
from newsclips2 import Article

class TestArticle(unittest2.TestCase):
    def test_get_date_by_url(self):
        a = Article("http://www.lvbusinesspress.com/articles/2011/11/28/news/iq_49033368.txt")
        self.assertEqual(a.date, date(2011, 11, 28))

        a = Article("http://www.lasvegassun.com/news/2011/nov/19/court-wants-nonprofit-group-pay-almost-1-million-r/")
        self.assertEqual(a.date, date(2011, 11, 19))

        a = Article("http://www.rgj.com/article/20111130/NEWS19/111130028/Group-files-suit-challenging-ability-public-employees-serve-legislature")
        self.assertEqual(a.date, date(2011, 11, 30))
