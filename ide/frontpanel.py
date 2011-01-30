from PyQt4.QtGui import * 
from PyQt4.QtCore import *

from pyview.ide.patterns import ObserverWidget

class FrontPanel(QWidget,ObserverWidget):
  
  """
  A QT instrument frontpanel.
  """
  
  def setInstrument(self,instrument):
    """
    Set the instrument variable of the frontpanel.
    """
    self.instrument = instrument
    self.instrument.attach(self)
    
  def __del__(self):
    print "Detaching instrument..."
    self.instrument.detach(self)
    
  def hideEvent(self,e):
    self.instrument.detach(self)
    QWidget.hideEvent(self,e)
    
  def showEvent(self,e):
    self.instrument.attach(self)
    QWidget.showEvent(self,e)
  
  def __init__(self,instrument,parent=None):
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self.setInstrument(instrument)


