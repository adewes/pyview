import sys

import os
import os.path

from conf.instruments import *

app = QApplication(sys.argv)

acqirisPanel = MyManager.frontPanel("acqiris")
acqiris = MyManager.getInstrument("acqiris")
acqirisPanel.requestConfigure()
import time
time.sleep(2)
for i in range(0,10):
  start = time.time()
  acqiris.bifurcationMap()
  acqiris.bifurcationMap()
  acqiris.bifurcationMap()
  print "%f seconds elapsed." % ((time.time()-start)/3)

MyManager.stop()