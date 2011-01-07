import sys
import getopt

sys.path.append('.')
sys.path.append('../')

from helpers.instrumentsmanager import *

MyManager = Manager()

MW3 = MyManager.getInstrument("agilent_mwg","TCPIP0::192.168.0.13::inst0")
MW2 = MyManager.instrumentCopy("agilent_mwg","agilent2","TCPIP0::192.168.0.13::inst0","Agilent 2")
MW1 = MyManager.instrumentCopy("agilent_mwg","agilent1","TCPIP0::192.168.0.12::inst0","Agilent 1")

print MW1.frequency()
print MW2.frequency()
print MW3.frequency()
print "Press [Enter] to continue..."

sys.stdin.readline()

MW1 = MyManager.reloadInstrument("agilent1")
MW2 = MyManager.reloadInstrument("agilent2")
#MW3 = MyManager.reloadInstrument("agilent_mwg")

print MW1.frequency()
print MW2.frequency()
print MW3.frequency()

MW4 = MyManager.getInstrument("agilent2")


app = QApplication(sys.argv)

Panel1 = MyManager.frontPanel("agilent1")
Panel2 = MyManager.frontPanel("agilent2")

MyMainWindow = QMainWindow()
CentralWidget = QWidget()
Splitter = QSplitter(Qt.Vertical)
Splitter.addWidget(Panel1)
Splitter.addWidget(Panel2)
MyMainWindow.setCentralWidget(Splitter)
MyMainWindow.show()

app.exec_()

MyManager.stop()


    
