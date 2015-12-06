import sys

from PyQt4.QtGui import * 
from PyQt4.QtCore import *
from PyQt4.uic import *

class NumericEdit(QLineEdit):
  
  def __init__(self,parent = None):
    QLineEdit.__init__(self)
    
  def getValue(self):
    return float(self.text())
    
  def setValue(self,value):
    self.setText("{0:g}".format((value)))
    
  def setRange(self,minimum,maximum):
    pass
    
  