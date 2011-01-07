import sys

import os
import os.path

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from ide.panel import *
from helpers.instrumentsmanager import *
from conf.instruments import *
from widgets.jba import JBAUtility
from ide.dashboard import InstrumentDashboard

app = QApplication(sys.argv)

MyPanel = Panel()

MyPanel.addWidget(MyManager.frontPanel("qubit1mwg"),1,1)
MyPanel.addWidget(MyManager.frontPanel("qubit2mwg"),2,1)
MyPanel.addWidget(MyManager.frontPanel("cavity1mwg"),3,1)
MyPanel.addWidget(MyManager.frontPanel("cavity2mwg"),4,1)
MyPanel.addWidget(MyManager.frontPanel("atts2"),5,1)
MyPanel.addWidget(MyManager.frontPanel("atts3"),6,1)
MyPanel.addWidget(MyManager.frontPanel("coil"),7,1)

try:
  AcqirisPanel = InstrumentDashboard("acqiris")
  AcqirisPanel.show()
except:
  print "Couldnt load Acqiris frontpanel..."

util = JBAUtility()
util.show()

MyPanel.show()
app.exec_()
MyManager.stop()