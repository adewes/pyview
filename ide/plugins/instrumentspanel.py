import sys

import os
import os.path
import string
import yaml
import pickle
import traceback
import time

from PyQt4.QtGui import * 
from PyQt4.QtCore import *

import shelve
import pyview.helpers.instrumentsmanager
from pyview.ide.patterns import ObserverWidget
from pyview.config.parameters import params

"""
Define the parameters and init functions of the plugin in the following dictionary.
"""

def restartPlugin(ide,*args,**kwargs):
  """
  This function restarts the plugin
  """
  if hasattr(ide,"instrumentsTab"):
    ide.tabs.removeTab(ide.tabs.indexOf(ide.instrumentsTab))
  instrumentsTab = InstrumentsPanel()
  ide.instrumentsTab = instrumentsTab
  ide.tabs.addTab(instrumentsTab,"Instruments")
  ide.tabs.setCurrentWidget(instrumentsTab)

def startPlugin(ide,*args,**kwargs):
  """
  This function starts the plugin
  """
  settingsMenu = ide.settingsMenu
  reloadInstrumentsTabEntry = settingsMenu.addAction("Reload Instruments Tab")
  ide.connect(reloadInstrumentsTabEntry,SIGNAL("triggered()"),lambda : reloadInstrumentsTab(ide))
  restartPlugin(ide,*args,**kwargs)


plugin = dict()
plugin["name"] = "Instruments Panel"
plugin["version"] = "1.0"
plugin["author.name"] = "Andreas Dewes"
plugin["author.email"] = "andreas.dewes@gmail.com"
plugin["functions.start"] = startPlugin
plugin["functions.stop"] = None
plugin["functions.restart"] = restartPlugin
plugin["functions.preferences"] = None

class InstrumentsArea(QMainWindow,ObserverWidget):

  def __init__(self,parent = None):
    QMainWindow.__init__(self,parent)
    ObserverWidget.__init__(self)
    
    self.setWindowTitle("Instruments")
    
    self._windows = dict()
    
    self.setAutoFillBackground(False)
    
    self._instrumentsArea = QMdiArea(self)

    self._instrumentsArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    self._instrumentsArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    self.setCentralWidget(self._instrumentsArea)

  def area(self):
    return self._instrumentsArea

  def removeFrontPanel(self,frontPanel):
    if frontPanel in self._windows and self._windows[frontPanel] in self._instrumentsArea.subWindowList():
      self._instrumentsArea.removeSubWindow(self._windows[frontPanel])
    
  def addFrontPanel(self,frontPanel):
    widget = self._instrumentsArea.addSubWindow(frontPanel)    
    self._windows[frontPanel] = widget
    widget.setWindowFlags(Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

class InstrumentList(QTreeWidget):

  def mouseDoubleClickEvent(self,e):
    QTreeWidget.mouseDoubleClickEvent(self,e)
    self.emit(SIGNAL("showFrontPanel()"))

class InstrumentsPanel(QWidget,ObserverWidget):

  def updatedGui(self,subject = None,property = None,value = None):
    if subject == self.manager:
      if property == "instruments":
        self.updateInstrumentsList()
      pass
  
  def updateInstrumentsList(self):
    instruments = self.manager.instruments()
    self.instrumentlist.clear()
    for instrument in sorted(instruments):
      item = QTreeWidgetItem()
      item.setText(0,instrument)
      item.setText(1,instruments[instrument]._name)
      item.setText(2,str(instruments[instrument].args()))
      item.setText(3,str(instruments[instrument].kwargs()))
      self.instrumentlist.insertTopLevelItem(self.instrumentlist.topLevelItemCount(),item)

  def reloadInstrument(self):
    selected = self.instrumentlist.selectedItems()
    for instrument in selected:
      print "Reloading %s" % instrument.text(0)
      self.manager.reloadInstrument(str(instrument.text(0)))

  def showFrontPanel(self):
    selected = self.instrumentlist.selectedItems()
    for instrument in selected:
      name = str(instrument.text(0))
      if name in self.dashboards:
        self.dashboards[name].hide()
        #self._instrumentsArea.removeFrontPanel(self.dashboards[name])
        del self.dashboards[name]
      panel = self.manager.frontPanel(name)
#      self._instrumentsArea.addFrontPanel(panel)
#      self._instrumentsArea.show()
      panel.show()
      self.dashboards[name] = panel
      panel.activateWindow()
  
  def restoreSetup(self):
    name = str(self.setupList.currentText())
    if name in self._states:
      self.manager.restoreState(self._states[name])
    
  def removeSetup(self):
    message = QMessageBox( )
    message.setWindowTitle("Confirm Setup Deletion")
    message.setIcon(QMessageBox.Question) 
    name = str(self.setupList.currentText())
    if name in self._states:
      message.setText("Do you really want to remove setup \"%s\"?" % name)
      message.setStandardButtons(QMessageBox.Cancel  | QMessageBox.Ok)
      message.setDefaultButton(QMessageBox.Cancel)
      result = message.exec_()
      if result == QMessageBox.Cancel:
        return
      del self._states[name]
    self.updateStateList()
    
  def saveSetup(self):
    name = str(self.setupList.currentText())

    #Sanitize the name of the setup...
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    name = ''.join(c for c in name if c in valid_chars)

    if name == "":
      return

    state = self.manager.saveState(name,withInitialization = False)
    self._states[name] = state
    self.saveStates()
    self.updateStateList()
    self.setupList.setCurrentIndex(self.setupList.findText(name))
    
  def saveStates(self,path = None):
    if path == None:
      path = self._picklePath
    string = yaml.dump(self._states)
    file = open(path,"w")
    file.write(string)
    file.close()
    
  def loadStates(self,path = None):
    if path == None:
      path = self._picklePath
    if os.path.exists(path):
      try:
        file = open(path,"r")
        string = file.read()
        self._states = yaml.load(string)
      except:
        print "Failed to load instrument setups!"
        traceback.print_exc()
        self._states = dict()
    else:
      self._states = dict()
    
  def updateStateList(self):  
    self.setupList.clear()
    for name in self._states.keys():
      self.setupList.addItem(name,name)
    
  def __init__(self,parent = None):
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self._instrumentsArea = InstrumentsArea()
    self.manager = pyview.helpers.instrumentsmanager.Manager()
    self.setMinimumHeight(200)
    settings = QSettings()
    if settings.contains("directories.setup"):
      setupPath = str(settings.value("directories.setup").toString())
    else:
      setupPath = os.getcwd()
    self._picklePath = setupPath+r"/config/setups.pickle"
    self.loadStates()
    self.dashboards = dict()
    self.setWindowTitle("Instruments")
    layout = QGridLayout()
        
    self.instrumentlist = InstrumentList()
    
    self.connect(self.instrumentlist,SIGNAL("showFrontPanel()"),self.showFrontPanel)
    
    self.instrumentlist.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.instrumentlist.setHeaderLabels(["Name","Base Class","Args","Kwargs"])
    
    
    self.setupList = QComboBox()
    self.setupList.setEditable(True)
    restoreSetup = QPushButton("Restore setup")
    saveSetup = QPushButton("Save setup")
    removeSetup = QPushButton("Remove setup")
    
    setupLayout = QBoxLayout(QBoxLayout.LeftToRight)
    
    reloadButton = QPushButton("Reload instrument")
    frontPanelButton = QPushButton("Show frontpanel")
    self.connect(reloadButton,SIGNAL("clicked()"),self.reloadInstrument)
    self.connect(frontPanelButton,SIGNAL("clicked()"),self.showFrontPanel)
    
    self.connect(restoreSetup,SIGNAL("clicked()"),self.restoreSetup)
    self.connect(saveSetup,SIGNAL("clicked()"),self.saveSetup)
    self.connect(removeSetup,SIGNAL("clicked()"),self.removeSetup)

    buttonsLayout = QBoxLayout(QBoxLayout.LeftToRight)
    buttonsLayout.addWidget(reloadButton)
    buttonsLayout.addWidget(frontPanelButton)
    buttonsLayout.addStretch()
    setupLayout.addWidget(restoreSetup)
    setupLayout.addWidget(saveSetup)
    setupLayout.addStretch()
    setupLayout.addWidget(removeSetup)

    layout.addWidget(self.instrumentlist)
    layout.addItem(buttonsLayout)
    layout.addWidget(QLabel("Store/restore setup:"))
    layout.addWidget(self.setupList)
    layout.addItem(setupLayout)
    self.manager.attach(self)   
    self.updateInstrumentsList()

    self.setLayout(layout)
    self.updateStateList()
