import sys

import os
import os.path

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from lib.wikidb import *

root = ArticleRoot()

children = root.children()

for article in children:
  print article
  print root.rowOfChild(article)
  grandchildren = article.children()
  for grandchild in grandchildren:
    print "My grandchild:"
    print grandchild
    print article.rowOfChild(grandchild)
