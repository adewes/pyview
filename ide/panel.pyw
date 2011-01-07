import sys
import getopt

import instruments
import frontpanels

import pyview.helpers.instrumentsmanager

from pyview.lib.classes import *

class Panel(QMainWindow,ReloadableWidget):

  def __init__(self,*args):
    ReloadableWidget.__init__(self)
    QMainWindow.__init__(self,None)

    menuBar = self.menuBar()
    
    fileMenu = menuBar.addMenu("File")
    self.widgets = []
    self.coordinates = []
        
        
    self.widget = QWidget()
    self.grid = QGridLayout()
    self.widget.setLayout(self.grid)
    self.setCentralWidget(self.widget)
    self.setWindowTitle("Instrument Panel")
    p = QPalette(self.palette())
    p.setColor(QPalette.Background, QColor(200,200,255))
    self.setPalette(p)
  
