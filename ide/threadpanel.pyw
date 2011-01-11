import sys

import os
import os.path
import string
import threading

from PyQt4.QtGui import * 
from PyQt4.QtCore import *

from pyview.lib.classes import *
from pyview.config.parameters import *


class ThreadPanel(QWidget,ObserverWidget,ReloadableWidget):

  def updatedGui(self,subject = None,property = None,value = None):
    pass
  
  def updateThreadList(self):
    threads = threading.enumerate()
    if threads == self._threads:
      return
    self._threads = threads
    self.threadlist.clear()
    for thread in threads:
      item = QTreeWidgetItem()
      item.setText(0,str(thread.name))
      item.setText(1,str(thread.ident))
      self.threadlist.insertTopLevelItem(self.threadlist.topLevelItemCount(),item)

  def killThread(self):
    selectedThreads = self.threadlist.selectedItems()
    threads = threading.enumerate()
    for selectedThread in selectedThreads:
      name = str(selectedThread.text(0))
      for thread in threads:
        if thread.name == name and hasattr(thread,"terminate"):
          print "Terminating thread..."
          thread.terminate()
    
  def __init__(self,parent = None):
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    ReloadableWidget.__init__(self)
    self.setMinimumHeight(200)
    self.setWindowTitle("Threads")
    layout = QGridLayout()
    self._threads = []
    
    self.threadlist = QTreeWidget()
    self.threadlist.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.threadlist.setHeaderLabels(["Name","Status"])
        
    setupLayout = QBoxLayout(QBoxLayout.LeftToRight)
    
    killButton = QPushButton("Kill")
    self.connect(killButton,SIGNAL("clicked()"),self.killThread)
    
    buttonsLayout = QBoxLayout(QBoxLayout.LeftToRight)
    buttonsLayout.addWidget(killButton)
    buttonsLayout.addStretch()

    layout.addWidget(self.threadlist)
    layout.addItem(buttonsLayout)

    self.updateThreadList()
    self.setLayout(layout)
    
    self.timer = QTimer(self)
    self.timer.setInterval(500)
    self.timer.start()
    self.connect(self.timer,SIGNAL("timeout()"),self.updateThreadList)
 