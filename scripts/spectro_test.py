import sys

import os
import os.path
from pylab import *

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

import helpers.instrumentsmanager

MyManager = helpers.instrumentsmanager.Manager()

acqiris = MyManager.getInstrument("acqiris")
acqiris = MyManager.reloadInstrument("acqiris")

qubit_mwg = MyManager.instrumentCopy("anritsu_mwg","anritsu1",kwargs ={"visaAddress": "GPIB0::4"})
MyManager.reloadInstrument("anritsu1")

cavity_mwg = MyManager.instrumentCopy("agilent_mwg","agilent1",kwargs = {"visaAddress" : "TCPIP0::192.168.0.12::inst0"})
cavity_mwg = MyManager.reloadInstrument("agilent1",kwargs = {"visaAddress":"TCPIP0::192.168.0.12::inst0"})

qubit_mwg.clear()
##
qubit_mwg.setFrequency(6)
qubit_mwg.setPower(6)
print qubit_mwg.frequency()
ps = []
fs = []
for f in arange(4.5,7.5,0.002):
	qubit_mwg.setFrequency(f)
	fs.append(f)
	p = acqiris.bifurcationMap()
	ps.append(p[0])
	cla()
	plot(fs,ps)
