import sys

import os
import os.path


import mimetypes
import threading

import random
import time


from PySide.QtGui import * 
from PySide.QtCore import *

from pyview.ide.wiki.articleeditor import *
from pyview.ide.filebrowser import *
from pyview.ide.preferences import *
from pyview.ide.params import *
from pyview.ide.wiki.articleview import *

class Wiki(QMainWindow):

  def __init__(self):
    QMainWindow.__init__(self)
    self.MainWidget = QWidget()
    Splitter = QSplitter(Qt.Horizontal)
    self.Editor = ArticleEditorWindow()
    self.Browser = BrowserWidget()
    self.Articles = ArticleTreeView()
    self.leftTabs = QTabWidget()
    self.leftTabs.addTab(self.Articles,"Articles")
    self.leftTabs.addTab(self.Browser,"File Browser")
    Splitter.addWidget(self.leftTabs)
    Splitter.addWidget(self.Editor)
    self.setCentralWidget(Splitter)
    self.connect(self.Articles,SIGNAL("openArticle(Article)"),self.openArticle)
    
  def openArticle(self,article):
    print "Opening article %s" % article.title

if __name__ == '__main__':
  app = QApplication(sys.argv)

  MyPrefs = Preferences()
  MyPrefs.init(filename = "wiki.dat")

  MyWindow = Wiki()
  MyWindow.show()

  app.exec_()