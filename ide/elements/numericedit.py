import sys

from PySide.QtGui import * 
from PySide.QtCore import *
from PySide.uic import *

class NumericEdit(QLineEdit):
  
  def __init__(self,parent = None):
    QLineEdit.__init__(self)
    
  def getValue(self):
    return float(self.text())
    
  def setValue(self,value):
    self.setText("%g" % (value))
    
  def setRange(self,minimum,maximum):
    pass
    
  