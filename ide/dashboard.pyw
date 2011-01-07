import sys
import getopt


import pyview.helpers.instrumentsmanager
from pyview.lib.classes import *

class InstrumentDashboard(QMainWindow):

  def reloadInstrument(self):
    print "Reloading instrument"
    self.instrument = self.Manager.reloadInstrument(self._instrument)
    self.frontpanel.setInstrument(self.instrument)

  def reloadFrontPanel(self):
    self.initFrontPanel()
      
  def reloadAll(self):
    self.reloadInstrument()
    self.reloadFrontPanel()
    import gc
    gc.collect()

  def initDashboard(self,*args):
    print "Loading front panel..."
    self.initInstrument()
    self.initFrontPanel()
    
  def initInstrument(self):
    print "Loading instrument..."
    self.instrument = self.Manager.getInstrument(self._instrument)
    print "Done."

  def initFrontPanel(self):
    if self.frontpanel != None:
        print "Detaching..."
        self.instrument.detach(self.frontpanel)
    self.frontpanel = self.Manager.frontPanel(self._instrument)
    self.setCentralWidget(self.frontpanel)
        

  def __init__(self,instrument,*args):

    self._instrument = instrument

    self.Manager = pyview.helpers.instrumentsmanager.Manager()

    QMainWindow.__init__(self,None)

    self.setWindowTitle("%s frontpanel" % instrument)
    self.frontpanel = None
    self.initDashboard(*args)
    
    menuBar = self.menuBar()
    
    fileMenu = menuBar.addMenu("File")
    
    reloadInstrument = fileMenu.addAction('Reload instrument')
    reloadFrontPanel = fileMenu.addAction('Reload frontpanel')
    reloadAll = fileMenu.addAction('Reload all')
    self.connect(reloadInstrument,SIGNAL("triggered()"),self.reloadInstrument)
    self.connect(reloadFrontPanel,SIGNAL("triggered()"),self.reloadFrontPanel)
    self.connect(reloadAll,SIGNAL("triggered()"),self.reloadAll)
    
    self.setAttribute(Qt.WA_DeleteOnClose,True)

if __name__ == '__main__':
  print "Loading frontpanel for instrument %s" % sys.argv[1]
  app = QApplication(sys.argv)
  dashboard = InstrumentDashboard(sys.argv[1],*(sys.argv[2:]))
  dashboard.show()
  app.exec_()
      
