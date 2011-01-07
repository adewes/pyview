import sys
import getopt

import time

import pyview.helpers.instrumentsmanager

from pyview.lib.canvas import *
from pyview.lib.classes import *
from pyview.ide.datamanager import *

#This is a simple data viewer.
class DataViewer(QMainWindow,ReloadableWidget,ObserverWidget):
  
  def selectCube(self,current,last):
    print "Current selection changed.."
    if not current == None:
      self.fastPlot.setDatacube(current._cube())

  def __init__(self,parent = None):
    QMainWindow.__init__(self,parent)
    ReloadableWidget.__init__(self)
    ObserverWidget.__init__(self)
    splitter = QSplitter(Qt.Horizontal)
    self.plotTabs = QTabWidget()
    self.propTabs = QTabWidget()
    self.props = QWidget()
    self.setWindowTitle("Data Viewer")
    splitter.addWidget(self.propTabs)
    splitter.addWidget(self.plotTabs)

    self.setCentralWidget(splitter)
    self.fastPlot = Plot2DWidget(None)
    self.plotTabs.addTab(self.fastPlot,"Fast Data Plotting")
    self.manager = dm.DataManager()
    self.datacubeList = DataTreeView()
    self.connect(self.datacubeList,SIGNAL("currentItemChanged(QTreeWidgetItem *,QTreeWidgetItem *)"),self.selectCube)
    self.datacubeList.setRoot(self.manager.root())
    self.propTabs.addTab(self.datacubeList,"Datacubes")
    
    
  