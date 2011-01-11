import sys

import os
import os.path
import string

from PyQt4.QtGui import * 
from PyQt4.QtCore import *

import shelve
import pyview.helpers.instrumentsmanager
from pyview.lib.classes import *
from pyview.ide.dashboard import InstrumentDashboard
from pyview.config.parameters import *

if 'pyview.ide.instrumentsarea' in sys.modules:
  reload(sys.modules['pyview.ide.instrumentsarea'])

from instrumentsarea import InstrumentsArea

#Directories should have been declared before...

class InstrumentsPanel(QWidget,ObserverWidget,ReloadableWidget):

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
        self._instrumentsArea.removeFrontPanel(self.dashboards[name])
#        del self.dashboards[name]
      panel = InstrumentDashboard(name)
      self._instrumentsArea.addFrontPanel(panel)
      self._instrumentsArea.show()
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
      self._states.sync()
    self.updateStateList()
    
  def saveSetup(self):
    selected = self.instrumentlist.selectedItems()
    selectedNames = map(lambda x:str(x.text(0)),selected)
    print selectedNames
    name = str(self.setupList.currentText())
    #Sanitize the name of the setup...
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    name = ''.join(c for c in name if c in valid_chars)
    if name == "":
      return
    state = self.manager.saveState(name,selectedNames)
    self._states[name] = state
    self._states.sync()
    self.updateStateList()
    self.setupList.setCurrentIndex(self.setupList.findText(name))
    
  def updateStateList(self):  
    self.setupList.clear()
    for name in self._states.keys():
      self.setupList.addItem(name,name)
    
  def __init__(self,parent = None):
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    ReloadableWidget.__init__(self)
    self._instrumentsArea = InstrumentsArea()
    self.manager = pyview.helpers.instrumentsmanager.Manager()
    self.setMinimumHeight(200)
    global params
    shelvePath = params["directories.setup"]+r"/config/setups.shelve"
    try:
      self._states = shelve.open(shelvePath)
    except:
      print "Unable to open measurement shelve at \"%s\"" % (shelvePath)
      pass
    self.dashboards = dict()
    self.setWindowTitle("Instruments")
    layout = QGridLayout()
        
    self.instrumentlist = QTreeWidget()
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
 