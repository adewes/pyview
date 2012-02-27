import sys

import os
import os.path
import string
import threading

from PyQt4.QtGui import * 
from PyQt4.QtCore import *

from pyview.config.parameters import *
from pyview.gui.patterns import ObserverWidget

class ThreadPanel(QWidget,ObserverWidget):

  def updatedGui(self,subject = None,property = None,value = None):
    pass
    
  def _updateItemInfo(self,item,identifier,thread):
    if identifier in self._threads and self._threads[identifier] == thread:
      return
    self._threads[identifier] = thread
    item.setText(0,str(thread["filename"]))
    item.setText(1,"running" if thread["isRunning"] else "failed" if thread["failed"] else "finished")
    item.setText(2,str(identifier))
    if self._editorWindow != None:
      editor = self._editorWindow.getEditorForFile(thread["filename"])
      if editor != None:
        editor.setTabText(" [-]" if thread["isRunning"] else " [!]" if thread["failed"] else " [.]")
        self._editorWindow.updateTabText(editor)
  
  def updateThreadList(self):
    threadDict = self._codeRunner.status()
    if threadDict == None or type(threadDict) != dict:
      return
    for identifier in threadDict:
      if identifier not in self._threadItems:
        item = QTreeWidgetItem()
        self._updateItemInfo(item,identifier,threadDict[identifier])
        self._threadView.insertTopLevelItem(self._threadView.topLevelItemCount(),item)
        self._threadItems[identifier] = item
      else:
        item = self._threadItems[identifier]
        self._updateItemInfo(item,identifier,threadDict[identifier])
    
    idsToDelete = []
    for identifier in self._threadItems:
      if not identifier in threadDict:
        item = self._threadItems[identifier]
        self._threadView.takeTopLevelItem(self._threadView.indexOfTopLevelItem(item))
        idsToDelete.append(identifier)
    
    for idToDelete in idsToDelete:
      del self._threadItems[idToDelete]
      
  def killThread(self):
    selectedItems = self._threadView.selectedItems()
    for selectedItem in selectedItems:
      if selectedItem in self._threadItems.values():
        identifier = filter(lambda x: x[0] == selectedItem,zip(self._threadItems.values(),self._threadItems.keys()))[0][1]
        self._codeRunner.stopExecution(identifier)
    
  def __init__(self,codeRunner = None,editorWindow = None,parent = None):
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self.setMinimumHeight(200)
    self.setWindowTitle("Thread Status")
    layout = QGridLayout()
    self._codeRunner = codeRunner
    self._editorWindow = editorWindow
    self._threads = {}
    self._threadItems = {}
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
 