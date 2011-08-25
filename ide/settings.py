from pyview.ide.plugins.instrumentspanel import *
from pyview.ide.plugins.threadpanel import *
import pyview.ide.plugins.measurementtool

import sys

import pyview.helpers.instrumentsmanager
import pyview.ide.datamanager
import pyview.ide.dataviewer

def showMeasurementTool(guiWindow):
  reload(sys.modules["pyview.ide.plugins.measurementtool"])
  tool = pyview.ide.plugins.measurementtool.MeasurementTool(codeRunner = guiWindow.codeRunner())
  tool.show()
  guiWindow._measurementTool = tool
  
def showDataManager(guiWindow):
  reload(sys.modules["pyview.ide.datamanager"])
  guiWindow.dataManager = pyview.ide.datamanager.DataManager(codeRunner = guiWindow.codeRunner())
  guiWindow.dataManager.show()
  
def reloadInstrumentsTab(ide):
  reload(sys.modules["pyview.ide.plugins.instrumentspanel"])
  if hasattr(ide,"instrumentsTab"):
    ide.tabs.removeTab(ide.tabs.indexOf(ide.instrumentsTab))
  instrumentsTab = sys.modules["pyview.ide.plugins.instrumentspanel"].InstrumentsPanel()
  ide.instrumentsTab = instrumentsTab
  ide.tabs.addTab(instrumentsTab,"Instruments")
  ide.tabs.setCurrentWidget(instrumentsTab)

def reloadThreadsTab(ide):
  reload(sys.modules["pyview.ide.plugins.threadpanel"])
  if hasattr(ide,"threadTab"):
    ide.tabs.removeTab(ide.tabs.indexOf(ide.threadTab))
  threadTab = sys.modules["pyview.ide.plugins.threadpanel"].ThreadPanel()
  ide.threadTab = threadTab
  ide.tabs.addTab(threadTab,"Threads")
  ide.tabs.setCurrentWidget(threadTab)

def InitIDE(ide):
  reloadInstrumentsTab(ide)
  reloadThreadsTab(ide)
  menubar = ide.menuBar()
  toolsMenu = ide.toolsMenu
  measurementTool = toolsMenu.addAction("&Measurement")
  dataManager = toolsMenu.addAction("&Data Manager")
  ide.connect(measurementTool,SIGNAL("triggered()"),lambda : showMeasurementTool(ide))
  ide.connect(dataManager,SIGNAL("triggered()"),lambda : showDataManager(ide))
  settingsMenu = ide.settingsMenu
  reinitCodeEnvironment = settingsMenu.addAction("Re-Init Code Environment")
  reloadInstrumentsTabEntry = settingsMenu.addAction("Reload instruments tab")
  reloadThreadsTabEntry = settingsMenu.addAction("Reload thread tab")
  ide.connect(reloadInstrumentsTabEntry,SIGNAL("triggered()"),lambda : reloadInstrumentsTab(ide))
  ide.connect(reloadThreadsTabEntry,SIGNAL("triggered()"),lambda : reloadThreadsTab(ide))
  ide.connect(reinitCodeEnvironment,SIGNAL("triggered()"),ide.setupCodeEnvironment)
