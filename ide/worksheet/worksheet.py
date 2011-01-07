import sys

import os
import os.path


import mimetypes
import threading

import random
import time


from PySide.QtGui import * 
from PySide.QtCore import *
from PySide import QtWebKit

from pyview.conf.parameters import *

class WorkSheet(QAbstractScrollArea):

  def resizeEvent(self,e):
    areaSize = self.viewport().size()
    widgetSize = self._editor.size()
    
    self.verticalScrollBar().setPageStep(self.height())
    self.horizontalScrollBar().setPageStep(self.width())
    self.verticalScrollBar().setRange(0, widgetSize.height()*2 - areaSize.height())
    self.horizontalScrollBar().setRange(0, widgetSize.width() - areaSize.width())

  def scrollContentsBy(self,x,y):
    print "Updating..."
    self.viewport().update()

  def paintEvent(self,e):
    
    painter = QPainter()
    
    painter.begin(self.viewport())
    

    hvalue = self.horizontalScrollBar().value()
    vvalue = self.verticalScrollBar().value()

    paintRect = QRectF(e.rect())
    
    paintRect.setLeft(5000)

    region = QRegion(paintRect)

    region.translate(1000,1000)
    
    self._editor.render(painter,sourceRegion = region)

    painter.drawEllipse(0,0,100,100)
    
    painter.end()

  def updateWidgetPosition(self):
    hvalue = self.horizontalScrollBar().value()
    vvalue = self.verticalScrollBar().value()
    topLeft = self.viewport().rect().topLeft()
    
    self._editor.move(topLeft.x() - hvalue, topLeft.y() - vvalue)    
     
  def __init__(self,parent = None):
    QAbstractScrollArea.__init__(self,parent)
    self._editor = QTextEdit()
    self._editor.setFixedHeight(20000)
    self.setFocusProxy(self._editor)
    
if __name__ == '__main__':
  print PYQT_VERSION_STR 
  app = QApplication(sys.argv)

  MyWindow = QMainWindow()
  
  workSheet = WorkSheet()

  MyWindow.setCentralWidget(workSheet)
  
  MyWindow.show()

  app.exec_()