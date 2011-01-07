import os.path
os.chdir("c:\projects\python\pylab")
sys.path.append('.')
sys.path.append('../')
import helpers.instrumentsmanager 
MyManager = helpers.instrumentsmanager.Manager()

MyManager.instrumentCopy("yokogawa","yoko2","GPIB0::9")
MyManager.instrument("agilent_mwg")
MyManager.reloadInstrument("yokogawa")
yoko = MyManager.instrument("yokogawa")
##
print yoko.voltage()