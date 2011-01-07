import sys

import os
import os.path


import mimetypes
import threading

import random
import time


from PyQt4.QtGui import * 
from PyQt4.QtCore import *

class Editor(QMainWindow):

  def __init__(self):
    QMainWindow.__init__(self)
    self.MainWidget = QWidget()
    Splitter = QSplitter(Qt.Horizontal)
    self.Area = QScrollArea()
    self.Editor = QTreeWidget()

    item = QTreeWidgetItem()
    item.setText(0,"Initialization")
    
    subitem = QTreeWidgetItem(item)
    subitem.setText(0,"Code")
    
    self.textEdit = QTextEdit()

    subsubitem = QTreeWidgetItem(subitem)    
    
    self.Editor.setItemWidget(subsubitem,0,self.textEdit)
    
    self.Editor.insertTopLevelItem(0,item)
    
    self.leftTabs = QTabWidget()
    self.Area.setWidget(self.Editor)
    self.setCentralWidget(self.Editor)
    
if __name__ == '__main__':
  app = QApplication(sys.argv)

  MyWindow = Editor()
  MyWindow.show()

  app.exec_()