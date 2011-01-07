import sys

import os
import os.path

import pyview.helpers.instrumentsmanager

MyManager = helpers.instrumentsmanager.Manager()

acqiris = MyManager.reloadInstrument("acqiris")
import time
time.sleep(10)
acqiris.AverageTrace(ntimes = 20)
print "Done"