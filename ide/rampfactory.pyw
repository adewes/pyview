import sys
import getopt

import helpers.instrumentsmanager

from pyview.lib.classes import *


class RampDetails(QWidget):
  pass  

class RampsWidget(QWidget):
  
  def __init__(self,parent = None):
    QWidget.__init__(self,parent)
    self.grid = QGridLayout()
    self.rampsList = QListWidget()
    self.selectedRamps = QListWidget()
    self.setLayout(self.grid)
    self.rampPanel = QWidget()
    self.addRampButton = QPushButton("Add Ramp")
    self.rampPanel.setMinimumWidth(200)
    self.grid.addWidget(QLabel("Ramps in the chain"),1,1)
    self.grid.addWidget(self.selectedRamps,2,1)
    self.grid.addWidget(self.rampPanel,1,2,1,2)
    self.grid.addWidget(self.addRampButton,3,1)
    
    self.connect(self.addRampButton,SIGNAL("triggered()"),self.addRamp)
    
  def addRamp(self):
    pass

class RampFactory(QMainWindow):

  def updateInstruments(self):
    self.instrumentNames = []
    self.instrumentControls = []
    self.instrumentMeasurements = []
    manager = helpers.instrumentsmanager.Manager()
    instruments = manager.instruments()
    for instrument in instruments:
      self.instrumentNames.append(instrument.name())
      self.instrumentControls.append(instrument.controls())
      self.instrumentMeasurements.append(instrument.measurements())
  
  def __init__(self,*args):
    QMainWindow.__init__(self,None)

    menuBar = self.menuBar()
    
    fileMenu = menuBar.addMenu("File")
    
    reloadInstrument = fileMenu.addAction('Reload instrument')
    reloadFrontPanel = fileMenu.addAction('Reload frontpanel')
    reloadAll = fileMenu.addAction('Reload all')
#    self.connect(reloadInstrument,SIGNAL("triggered()"),self.reloadInstrument)
#    self.connect(reloadFrontPanel,SIGNAL("triggered()"),self.reloadFrontPanel)
#    self.connect(reloadAll,SIGNAL("triggered()"),self.reloadAll)
    
#    self._MyTimer = QTimer(self)
#    self.connect(self._MyTimer,SIGNAL("timeout()"),self.onTimer)
#    self._MyTimer.start(100)
  
    self.widget = RampsWidget()
    self.setCentralWidget(self.widget)
    self.setWindowTitle("Ramp Factory")
    
    
