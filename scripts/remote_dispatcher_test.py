import sys
import os

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from helpers.instrumentsmanager import *
from lib.classes import *
from conf.instruments import *

MyManager = Manager()

mwg = MyManager.remoteInstrument('http://localhost:8000',"qubit1","anritsu_mwg",[],{'name' : 'Qubit 1','visaAddress' : "GPIB0::4"})

class MwgObserver:

  def __init__(self,mwg):
    mwg.attach(self)
    print "Attached..."
    
  def updated(self,subject,property = None,value = None):
    print "Property {0!s} got updated!".format(property)

o = MwgObserver(mwg)

print mwg.frequency()
mwg.dispatch("frequency")
import time
time.sleep(1)