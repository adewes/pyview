import sys

import os
import os.path

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from xml.dom.minidom import Document
from xml.dom.minidom import parse, parseString


import sys
import os

import time

from PySide.QtGui import * 
from PySide.QtCore import *
from PySide.uic import *
from math import *

from numpy import *
from pylab import *

def frexp10(x):
	if x == 0:
		return 0,0
	exponent = math.floor(math.log10(math.fabs(x)))
	mantissa = x/math.pow(10,exponent)
	return mantissa,exponent
	
def generateTicks(minValue,maxValue,n = 10,strict = False):
  
  if minValue > maxValue:
    swap = minValue
    minValue = maxValue
    maxValue = swap
  
  diffx = maxValue-minValue
  diff_m,diff_e = frexp10(diffx/float(n-1))
  
  diff_m = ceil(diff_m)
  
  minscale = floor(minValue/diff_m/pow(10,diff_e))*pow(10,diff_e)*diff_m
  maxscale = ceil(maxValue/diff_m/pow(10,diff_e))*pow(10,diff_e)*diff_m
  
  currentValue = minscale
  
  ticks = []
  
  
  if strict:
    increment =(maxscale-minscale)/(float(n)-1)
  else:
    increment = diff_m*pow(10,diff_e)

  while currentValue <= maxscale:
    if currentValue >= minValue and currentValue <= maxValue:
      ticks.append(currentValue)
    currentValue += increment
    currentValue = currentValue
  return ticks

class XYPlot(QLabel):

  def clear(self):
    self.xData = []
    self.yData = []
    self.transformedPoints = []
    self.dataBounds = []
    self.dataRect = QRectF(0,0,100,100)
    self.viewRect = self.dataRect
    self._zoomRects = []

    self.recalculateBounds()
  
  def __init__(self,title = "",parent = None):
    QLabel.__init__(self,parent)
    self.borderX= 0.1
    self.borderY = 0.1
    self._xtics = 5.0
    self._ytics = 5.0
    self._zooming = False
    self.screenZoomRect = QRectF()
    self.viewRect = None
    self.paintRect = QRectF()

    self.setMinimumWidth(400)
    self.setMinimumHeight(200)
    self.setMouseTracking(True)

    self.clear()

    self.fontSize = 12
    self.title = title
    self.colors = ["red","blue","green","magenta","yellow","cyan"]
    self.rotation =0

  def resizeEvent(self,event):
    self.fontSize = min(self.width(),self.height())*min(self.borderX,self.borderY)/2.0
    self.paintRect.setRect(self.width()*self.borderX,self.height()*self.borderY,self.width()*(1.0-self.borderX*2.0),self.height()*(1.0-self.borderY*2.0))
    
  def setData(self,index,x,y):
    ax = array(x)
    ay = array(y)
    while len(self.xData) <= index:
      self.xData.append(array([]))
    while len(self.yData) <= index:
      self.yData.append(array([]))
    self.xData[index] = ax
    self.yData[index] = ay
    bounds = QRectF(min(ax),min(ay),max(ax)-min(ax),max(ay)-min(ay))
    while len(self.dataBounds) <= index:
      self.dataBounds.append(QRectF())
    self.dataBounds[index] = bounds
    self.recalculateBounds(updateLimits = False)
    self.transformData(index)
    self.update()
        
  def addData(self,x,y):
    return self.updateData(len(self.xData),x,y)
    
  def recalculateBounds(self,updateLimits = True):
    
    minX = None
    maxX = None
    minY = None
    maxY = None
    
    for i in range(0,len(self.xData)):
      mxx = self.dataBounds[i].right()
      if mxx > maxX or maxX == None:
        maxX = mxx
      mnx = self.dataBounds[i].left()
      if mnx < minX or minX == None:
        minX = mnx
    for i in range(0,len(self.yData)):
      mxy = self.dataBounds[i].bottom()
      if mxy > maxY or maxY == None:
        maxY = mxy
      mny = self.dataBounds[i].top()
      if mny < minY or minY == None:
        minY = mny
    
    if minX == None:
      minX = 0
    if maxX == None:
      maxX = 0
    if maxY == None:
      maxY = 0
    if minY == None:
      minY = 0
    
    if minX == maxX:
      minX -= 1
      maxX+=1
    
    if minY == maxY:
      minY-=1
      maxY+=1
    
    self.dataRect.setRect(minX,minY,maxX-minX,maxY-minY)
    if updateLimits or len(self._zoomRects) == 0:
      self.setLimits(self.dataRect)
        
  def transformData(self,i):
    xdata = self.xData[i]
    ydata = self.yData[i]
    Path = QPainterPath()
    lastPoint = QPointF(xdata[0],ydata[0])
    Path.moveTo(lastPoint)
    scanRange = range(0,len(xdata))
    lastSlope = None
    cnt = 0
    w = self.dataRect.width()
    h = self.dataRect.height()
    for j in scanRange:
      currentPoint = QPointF(xdata[j],ydata[j])
      a = ((currentPoint.y()-lastPoint.y())/h)
      b = ((currentPoint.x()-lastPoint.x())/w)
      if b != 0:
        slope = a/b
      else:
        if (a>0 and b >0) or (a < 0 and b < 0):
          slope = 1e999
        else:
          slope = -1e999
      if lastSlope != None and math.fabs(slope-lastSlope) < 0.001:
        pass
      else:
        Path.lineTo(lastPoint)
        cnt+=1
        lastSlope = slope
      lastPoint = currentPoint
    print cnt," points used (instead of {0:d}).".format(len(scanRange))
    Path.lineTo(currentPoint)
    while len(self.transformedPoints) <= i:
      self.transformedPoints.append(QPainterPath())
    self.transformedPoints[i] = Path     
    
  def transform(self,x,y):
    return (x-self.dataRect.left())/self.dataRect.width()*self.paintRect.width(),(1.0-(y-self.dataRect.top())/self.dataRect.height())*self.paintRect.height()
  
  def screenX(self,x):
    return (self.borderX+(x-self.viewRect.left())/self.viewRect.width()*(1.0-2.0*self.borderX))*self.width()

  def screenY(self,y):
    return ((1.0-self.borderX)-(y-self.viewRect.top())/self.viewRect.height()*(1.0-2.0*self.borderY))*self.height()
    
  def limits(self):
    return self.viewRect
    
  def setLimits(self,rect):
    self.viewRect = rect
    self.update()
    self.emit(SIGNAL("limitsChanged(QRectF)"),self.viewRect)
    
  def setXLimits(self,low = None,high = None):
    viewRect = QRectF(self.viewRect)
    if low != None:
      viewRect.setLeft(low)
    if high != None:
      viewRect.setRight(high)
    self.setLimits(viewRect)
    
  def setYLimits(self,low = None,high = None):
    viewRect = QRectF(self.viewRect)
    if low != None:
      viewRect.setTop(low)
    if high != None:
      viewRect.setBottom(high)
    self.setLimits(viewRect)
    
  def paintEvent(self,e): 
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing, True);
    painter.setPen(QPen(Qt.black, 1, Qt.SolidLine, Qt.RoundCap));
    oldBrush = painter.brush()
    brush = QBrush(QColor(255,255,255))
    painter.setBrush(brush)
    painter.drawRect(self.paintRect.left(),self.paintRect.top(),self.paintRect.width(),self.paintRect.height())    
    painter.setBrush(oldBrush)
    painter.setFont(QFont("Arial", self.fontSize*1.2));
    metrics = QFontMetrics(painter.font())
    rect = metrics.boundingRect(self.title)
    painter.drawText(self.borderX*self.width(),0,self.paintRect.width(),rect.height(),Qt.AlignCenter,self.title)
    painter.setFont(QFont("Arial", self.fontSize))
    metrics = QFontMetrics(painter.font())

    viewRect = self.viewRect

    ticks = generateTicks(viewRect.left(),viewRect.right(),8)

    for tick in ticks:
      text = "{0:g}".format(tick)
      screenCoordinate = self.screenX(tick)
      rect = metrics.boundingRect(text)
      painter.drawText(screenCoordinate-rect.width()/2.0,self.height()*(1.0-self.borderY)+ rect.height(),text)

    ticks = generateTicks(viewRect.top(),viewRect.bottom(),7)

    for tick in ticks:
      text = "{0:g}".format(tick)
      screenCoordinate = self.screenY(tick)
      rect = metrics.boundingRect(text)
      painter.drawText(0,screenCoordinate-rect.height()/2,self.width()*self.borderX-4,rect.height(),Qt.AlignRight,text)

    if self._zooming:
      painter.drawRect(self.screenZoomRect.left(),self.screenZoomRect.top(),self.screenZoomRect.width(),self.screenZoomRect.height())


    painter.translate(self.paintRect.left()-viewRect.left()*self.paintRect.width()/viewRect.width(),self.paintRect.top()+viewRect.bottom()*self.paintRect.height()/viewRect.height())
    painter.scale(self.paintRect.width()/viewRect.width(),-self.paintRect.height()/viewRect.height())

    painter.setClipRect(viewRect)
    painter.setClipping(True)

    for j in range(0,len(self.transformedPoints)):
      painter.setPen(QColor(self.colors[j%len(self.colors)]))
      painter.drawPath(self.transformedPoints[j])
      
  def _screenZoomTo(self,rect):
    self._zoomRects.append(self.limits())
    rect = rect.normalized()
    self.setLimits(QRectF(self.viewRect.left()+(rect.left()-self.paintRect.left())/self.paintRect.width()*self.viewRect.width(),self.viewRect.top()+(1.0-(rect.bottom()-self.paintRect.top())/self.paintRect.height())*self.viewRect.height(),self.viewRect.width()*rect.width()/self.paintRect.width(),self.viewRect.height()*rect.height()/self.paintRect.height()))
    self.update()
      
  def mouseMoveEvent(self,e):
    if self._zooming:
      self.screenZoomRect.setRight(e.x())
      self.screenZoomRect.setBottom(e.y())
      self.update()
    
  def mousePressEvent(self,e):
    if e.button() == Qt.LeftButton:
      self.screenZoomRect.setLeft(e.x())
      self.screenZoomRect.setTop(e.y())
      self._zooming = True
    elif e.button() == Qt.RightButton:
      if len(self._zoomRects) > 0: 
        self.setLimits(self._zoomRects.pop())
      else:
        self.setLimits(self.dataRect)
    
  def mouseReleaseEvent(self,e):
    if e.button() == Qt.LeftButton:
      self.screenZoomRect.setRight(e.x())
      self.screenZoomRect.setBottom(e.y())
      self._zooming = False
      if math.fabs(self.screenZoomRect.width()) < 10 or math.fabs(self.screenZoomRect.height()) < 10:
        self.update()
        return
      self._screenZoomTo(self.screenZoomRect)