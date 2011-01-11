from pyview.ide.instrumentspanel import *
from pyview.ide.threadpanel import *


import pyview.helpers.instrumentsmanager
import pyview.ide.measurementtool
import pyview.ide.scriptingtool
import pyview.ide.datamanager
import pyview.ide.dataviewer
import sys


from pyview.ide.panel import Panel


def showPanel(guiWindow):
  MyManager = pyview.helpers.instrumentsmanager.Manager()
  
  if hasattr(guiWindow,"instrumentsPanel"):
    guiWindow.instrumentsPanel.close()
  
  panel = QMainWindow()
  panel.setWindowTitle("Instruments")

  panel.setDockOptions(QMainWindow.AllowNestedDocks | QMainWindow.VerticalTabs )

  manager = pyview.helpers.instrumentsmanager.Manager()

  afg1 = manager.frontPanel("afg1")
  afg2 = manager.frontPanel("afg2")
  afg3 = manager.frontPanel("afg3")

  panel.dock1 = QDockWidget(panel)
  panel.dock2 = QDockWidget(panel)
  panel.dock3 = QDockWidget(panel)
  
  
  panel.dock1.setWidget(afg1)
  panel.dock2.setWidget(afg2)
  panel.dock3.setWidget(afg3)



  panel.show()
  
  guiWindow.instrumentsPanel = panel


def showScriptingTool(guiWindow):
  reload(sys.modules["pyview.ide.scriptingtool"])
  tool = pyview.ide.scriptingtool.ScriptingTool()
  tool.show()
  guiWindow._scriptingTool = tool

def showMeasurementTool(guiWindow):
  reload(sys.modules["pyview.ide.measurementtool"])
  tool = pyview.ide.measurementtool.MeasurementTool()
  tool.show()
  guiWindow._measurementTool = tool
  
def showDataManager(guiWindow):
  reload(sys.modules["pyview.ide.datamanager"])
  guiWindow.dataManager = pyview.ide.datamanager.DataManager()
  guiWindow.dataManager.show()
  
def reloadInstrumentsTab(ide):
  print "Reloading..."
  reload(sys.modules["pyview.ide.instrumentspanel"])
  if hasattr(ide,"instrumentsTab"):
    ide.tabs.removeTab(ide.tabs.indexOf(ide.instrumentsTab))
  instrumentsTab = sys.modules["pyview.ide.instrumentspanel"].InstrumentsPanel()
  ide.instrumentsTab = instrumentsTab
  ide.tabs.addTab(instrumentsTab,"Instruments")
  ide.tabs.setCurrentWidget(instrumentsTab)

def reloadThreadsTab(ide):
  print "Reloading..."
  reload(sys.modules["pyview.ide.threadpanel"])
  if hasattr(ide,"threadTab"):
    ide.tabs.removeTab(ide.tabs.indexOf(ide.threadTab))
  threadTab = sys.modules["pyview.ide.threadpanel"].ThreadPanel()
  ide.threadTab = threadTab
  ide.tabs.addTab(threadTab,"Threads")
  ide.tabs.setCurrentWidget(threadTab)

    
def InitIDE(ide):
  reloadInstrumentsTab(ide)
  reloadThreadsTab(ide)
  menubar = ide.menuBar()
  toolsMenu = ide.toolsMenu
  measurementTool = toolsMenu.addAction("&Measurement")
  scriptingTool = toolsMenu.addAction("&Scripting")
  instrumentsPanel = toolsMenu.addAction("&Instruments Panel")
  dataManager = toolsMenu.addAction("&Data Manager")
  ide.connect(measurementTool,SIGNAL("triggered()"),lambda : showMeasurementTool(ide))
  ide.connect(scriptingTool,SIGNAL("triggered()"),lambda : showScriptingTool(ide))
  ide.connect(instrumentsPanel,SIGNAL("triggered()"),lambda : showPanel(ide))
  ide.connect(dataManager,SIGNAL("triggered()"),lambda : showDataManager(ide))
  settingsMenu = ide.settingsMenu
  reinitCodeEnvironment = settingsMenu.addAction("Re-Init code environment")
  reloadInstrumentsTabEntry = settingsMenu.addAction("Reload instruments tab")
  reloadThreadsTabEntry = settingsMenu.addAction("Reload thread tab")
  ide.connect(reloadInstrumentsTabEntry,SIGNAL("triggered()"),lambda : reloadInstrumentsTab(ide))
  ide.connect(reloadThreadsTabEntry,SIGNAL("triggered()"),lambda : reloadThreadsTab(ide))
  ide.connect(reinitCodeEnvironment,SIGNAL("triggered()"),ide.setupCodeEnvironment)
  
  
#print "Done with settings"