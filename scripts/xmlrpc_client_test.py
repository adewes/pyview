import sys
import os
import weakref

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from helpers.instrumentsmanager import *
from lib.classes import *

import xmlrpclib

s = xmlrpclib.ServerProxy('http://localhost:8000')
#print s.div(5,2)  # Returns 5//2 = 2
s.instrument("qubit1","anritsu_mwg",[],{'name' : 'Qubit 1','visaAddress' : "GPIB0::4"})
s.instrument("qubit2","anritsu_mwg",[],{'name' : 'Qubit 2','visaAddress' : "GPIB0::6"})
s.instrument("temperature")

afg1 = RemoteInstrument(s,"afg1","afg",[],{"name": "AFG Channel 1"})
afg2 = RemoteInstrument(s,"afg2","afg",[],{"name": "AFG Channel 2","source":2})

print afg1.offset()
print afg2.offset()

mwg = RemoteInstrument(s,"qubit1mwg","anritsu_mwg",[],{'name' : 'Qubit 1','visaAddress' : "GPIB0::4"})
mwg.start()
print mwg.setFrequency(5.0)
mwg.reloadInstrument()
print "Qubit 1 frequency: %g " % mwg.frequency()

#The Acqiris card
#acqiris = RemoteInstrument(s,"acqiris","acqiris",kwargs = {'name': 'Acqiris Card'})