#!/usr/bin/env python

import sys
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtWebKit import *

app = QApplication(sys.argv)


web = QWebView()

web.load(QUrl("http://google.com"))
web.show()

sys.exit(app.exec_())
