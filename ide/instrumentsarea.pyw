import sys
import getopt


from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtWebKit import *
from pyview.ide.preferences import *
import pickle
import cPickle
import copy

from pyview.lib.patterns import ObserverWidget,KillableThread
if 'pyview.lib.ramps' in sys.modules:
  reload(sys.modules['pyview.lib.ramps'])
from pyview.lib.ramps import *
from pyview.conf.parameters import *
from pyview.lib.datacube import Datacube
from pyview.helpers.datamanager import DataManager
from pyview.helpers.instrumentsmanager import Manager
from pyview.lib.classes import *

class InstrumentsArea(QMainWindow,ObserverWidget):

  def __init__(self,parent = None):
    QMainWindow.__init__(self,parent)
    ObserverWidget.__init__(self)
    
    self.setWindowTitle("Instruments")
    
    self._windows = dict()
    
    self.setAutoFillBackground(False)
    
    self._instrumentsArea = QMdiArea(self)

    self._instrumentsArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    self._instrumentsArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    self.setCentralWidget(self._instrumentsArea)

  def area(self):
    return self._instrumentsArea

  def removeFrontPanel(self,frontPanel):
    if frontPanel in self._windows and self._windows[frontPanel] in self._instrumentsArea.subWindowList():
      self._instrumentsArea.removeSubWindow(self._windows[frontPanel])
    
  def addFrontPanel(self,frontPanel):
    widget = self._instrumentsArea.addSubWindow(frontPanel)    
    self._windows[frontPanel] = widget
    widget.setWindowFlags(Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
