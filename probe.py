#!/usr/bin/env python

import code
import argparse
from core.parsers.article import Article

parser = argparse.ArgumentParser()
parser.add_argument("url")
args = parser.parse_args()

article = Article(args.url)
code.interact(local=dict(article=article, tree=article.tree))
