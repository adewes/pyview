import sys

import os
import os.path
import string
import threading

from PyQt4.QtGui import * 
from PyQt4.QtCore import *

from pyview.config.parameters import *
from pyview.ide.patterns import ObserverWidget

class ThreadPanel(QWidget,ObserverWidget):

  def updatedGui(self,subject = None,property = None,value = None):
    pass
  
  def updateThreadList(self):
    threadDict = self._codeRunner.status()
    if threadDict == self._threadDict:
      return
    self._threadDict = threadDict
    self._threadView.clear()
    self._identifiers = {}
    for identifier in threadDict:
      if threadDict[identifier]["isRunning"] == False and threadDict[identifier]["failed"] == False:
        continue
      item = QTreeWidgetItem()
      item.setText(2,str(identifier))
      item.setText(0,str(threadDict[identifier]["filename"]))
      item.setText(1,"running" if threadDict[identifier]["isRunning"] else "failed" if threadDict[identifier]["failed"] else "finished")
      self._identifiers[self._threadView.topLevelItemCount()] = identifier
      self._threadView.insertTopLevelItem(self._threadView.topLevelItemCount(),item)

  def killThread(self):
    selectedItems = self._threadView.selectedItems()
    for selectedItem in selectedItems:
      identifier = self._identifiers[self._threadView.indexOfTopLevelItem(selectedItem)]
      self._codeRunner.stopExecution(identifier)
    
  def __init__(self,codeRunner = None,parent = None):
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self.setMinimumHeight(200)
    self.setWindowTitle("Thread Status")
    layout = QGridLayout()
    self._codeRunner = codeRunner
    self._threadDict = {}
    self._identifiers = {}
    self._threadView = QTreeWidget()
    self._threadView.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self._threadView.setHeaderLabels(["filename","status","identifier"])
        
    setupLayout = QBoxLayout(QBoxLayout.LeftToRight)
    
    killButton = QPushButton("Kill")
    self.connect(killButton,SIGNAL("clicked()"),self.killThread)
    
    buttonsLayout = QBoxLayout(QBoxLayout.LeftToRight)
    buttonsLayout.addWidget(killButton)
    buttonsLayout.addStretch()

    layout.addWidget(self._threadView)
    layout.addItem(buttonsLayout)

    self.updateThreadList()
    self.setLayout(layout)
    
    self.timer = QTimer(self)
    self.timer.setInterval(500)
    self.timer.start()
    self.connect(self.timer,SIGNAL("timeout()"),self.updateThreadList)
 