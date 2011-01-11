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
from PySide.QtOpenGL import *
import objects
import objectview
import propertyview
import pyview.ide.datacubeview as datacubeview
from pyview.lib.datacube import Datacube

from pyview.config.parameters import *

class MyScene(QGraphicsScene):

  def resolution(self):
    return self._resolution
    
  def setResolution(self,resolution):
    for item in self.items():
      item.changeResolution(self._resolution,resolution)
    self._resolution = resolution

  def mouseDoubleClickEvent(self,e):
    items = self.items(e.scenePos(),Qt.IntersectsItemShape,Qt.AscendingOrder)
    for item in items:
      if item.parent() == self.topLevelItem():
        print "Setting top level item to %s" % item.name()
        self.setTopLevelItem(item)
        return
    print "Unsetting top level item..."
    if self.topLevelItem() != None:
      self.setTopLevelItem(self.topLevelItem().parent())
    else:
      self.setTopLevelItem(None)
    

  def topLevelItem(self):
    return self._topLevelItem

  def setTopLevelItem(self,topLevelItem):
    if topLevelItem != None:
      self._topLevelItem = topLevelItem
    else:
      self._topLevelItem = self._rootItem
    self.clearSelection()
    self.invalidate()
    
  def processNewSelection(self):
    for item in self.selectedItems():
      if item.parent() != self._topLevelItem:
        item.setSelected(False)
    if len(self.selectedItems()) == 1:
      self.selectedItems()[0].grabMouse()
    elif self.mouseGrabberItem() != None:
      self.mouseGrabberItem().ungrabMouse()
    
  def setRootItem(self,rootItem):
    self._rootItem = rootItem
    self.setTopLevelItem(None)
    
  def __init__(self,parent = None,rootItem = None,resolution = 600):
    QGraphicsScene.__init__(self,parent)
    self._dragging = False
    self._selecting = False
    self._resolution = resolution
    self._rootItem = rootItem
    self._addToSelection = False
    self.setTopLevelItem(None)
    self._editorItem = None
    self._topLevelItemClipped = False
    self.connect(self,SIGNAL("selectionChanged()"),self.processNewSelection)
  
  def mouseMoveEvent(self,e):
    if self._selecting:
      self._currentPos = e.scenePos()
      self.invalidate(layers = QGraphicsScene.ForegroundLayer) 
    if self._dragging:
      for item in self.selectedItems():
        mapFunc = lambda x: item.mapToParent(item.mapFromScene(x))
        diff = mapFunc(e.scenePos())-mapFunc(self._startPos)
        item.moveBy(diff.x(),diff.y())
        item.notify("position",item.scenePos())
        self.invalidate(layers = QGraphicsScene.ForegroundLayer)
      self._startPos = e.scenePos()
    QGraphicsScene.mouseMoveEvent(self,e)

  def keyPressEvent(self,e):
    if e.key() == Qt.Key_Control:
      self._addToSelection = True
      
  def keyReleaseEvent(self,e):
    if e.key() == Qt.Key_Control:
      self._addToSelection = False

  def mousePressEvent(self,e):
    if self.mouseGrabberItem() != None:
      QGraphicsScene.mousePressEvent(self,e)
    if e.isAccepted():
      print "Press accepted"
      return
    items = self.items(e.scenePos(),Qt.IntersectsItemShape,Qt.AscendingOrder)
    selectedItems = self.selectedItems()
    foundSelectedItem = False
    if len(items) == 0:
      self.clearSelection()
    elif len(selectedItems) > 0:
      for item in items: 
        if item in selectedItems:
          foundSelectedItem = True
          break
    if foundSelectedItem == False:
      if not self._addToSelection:
        self.clearSelection()
      for item in items:
        if item.parent() == self.topLevelItem():
          item.setSelected(True)
          foundSelectedItem = True
          break
    if foundSelectedItem:
      self._dragging = True
    else:
      self._selecting = True
      self._currentPos = e.scenePos()
    self._startPos = e.scenePos()

  def mouseReleaseEvent(self,e):
    QGraphicsScene.mouseReleaseEvent(self,e)
    if self._selecting:
      self.clearSelection()
      items = self.items(QRectF(self._startPos,e.scenePos()),Qt.IntersectsItemShape,Qt.AscendingOrder)
      for item in items:
        if item.parent() == self.topLevelItem():
          item.setSelected(True)
      self.invalidate(layers = QGraphicsScene.ForegroundLayer)
    self._dragging = False
    self._selecting = False
    
class MyGraphicsView(QGraphicsView):

  def __init__(self,parent = None):
    QGraphicsView.__init__(self,parent)
    
  def adjustSceneDimensions(self):
    self._sceneWidthMm = 100
    self._sceneHeightMm = 100
    
    self._sceneWidthPixel  = 600*self._sceneWidthMm/25.4
    self._sceneHeightPixel = 600*self._sceneHeightMm/25.4
    
    self.scene().setSceneRect(QRectF(0,0,self._sceneWidthPixel,self._sceneHeightPixel))
    self.setSceneRect(self.scene().sceneRect())

    transform = QTransform()
    
    transform.scale(self.contentsRect().width()/self.sceneRect().width(),self.contentsRect().height()/self.sceneRect().height())
    
    self.setTransform(transform)

  def paintEvent(self,event):

    QGraphicsView.paintEvent(self,event)
    
    painter = QPainter(self.viewport())
    
    self.paintManipulators(painter,event.rect())
    
  
  def paintManipulators(self,painter,rect):
    
    scene = self.scene()
    
    scene.invalidate()
    
    sceneToView = lambda x : self.mapFromScene(x)
    
    if len(scene.selectedItems()) > 0:
      
      rect = QRectF()

      pen = QPen()
      
      pen.setColor(QColor(100,240,0))
      pen.setWidthF(2.0)
      pen.setStyle(Qt.DotLine)
      
      painter.setPen(pen)
      
      
      for item in scene.selectedItems():
        item.paintManipulators(painter,self)
        painter.drawPolygon(sceneToView(item.mapToScene(item.boundingRect())))
      
      if len(scene.selectedItems()) == 1:
        item = scene.selectedItems()[0]
        rect = sceneToView(item.mapToScene(item.boundingRect()).boundingRect())
      
    if scene.topLevelItem() != None:
      pen = QPen()
      
      pen.setColor(QColor(240,100,0))
      pen.setWidthF(4.0)
      pen.setStyle(Qt.DashLine)
      
      painter.setPen(pen)

      painter.drawPolygon(sceneToView(scene.topLevelItem().mapToScene(scene.topLevelItem().boundingRect())))

    if scene._selecting:
      pen = QPen()
      
      pen.setColor(QColor(100,100,0))
      pen.setWidthF(2.0)
      pen.setStyle(Qt.DotLine)
      
      painter.setPen(pen)
      painter.drawPolygon(sceneToView(QRectF(scene._startPos,scene._currentPos)))


  def setScene(self,scene):
    QGraphicsView.setScene(self,scene)
    self.adjustSceneDimensions()

  def keyPressEvent(self,e):
    print "Key pressed!"
    if e.key() == Qt.Key_F1:
      print "Printing scene..."
      self.printScene()

  def printScene(self):
  
    printer = QPrinter()
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName("test.pdf")
    printer.setPaperSize(QSizeF(self._sceneWidthMm,self._sceneHeightMm),QPrinter.Millimeter)
    printer.setResolution(600)
    printer.setPageMargins(0,0,0,0,QPrinter.Millimeter)

    painter = QPainter()
    
    painter.begin(printer)

    self.scene().render(painter,source = self.sceneRect())
    
    painter.end()

  def resizeEvent(self,e):
    self.adjustSceneDimensions()
    QGraphicsView.resizeEvent(self,e)
    
class Editor(QMainWindow):

    

  def __init__(self):
    QMainWindow.__init__(self)
    
    self.scene = MyScene()
    self.view = MyGraphicsView()
    self.view.setScene(self.scene)
    self.view.setMouseTracking(True)
    
    self.setMinimumWidth(640)
    self.setMinimumHeight(480)
    
    
    self._root = objects.Root(name = "root")
    
    self.scene.addItem(self._root)

    self.scene.setRootItem(self._root)

#    self.edit = objects.LineEditor(parent = self._root,name = "test edit")

    self.tabs = QTabWidget()
    
    from numpy import complex128
    
    self._cube = Datacube()
    self._cube.addVariables(["x","y","z"])
    self._cube.set(x = 1,y = 2,z = 3)
    self._cube.commit()
    
    print self.view.physicalDpiX() 
    
    print "length:",len(self._cube)
    
    self.propertyview = propertyview.PropertyTreeView(self._root)
    self.objectview = objectview.ObjectTreeView(self._root,propertyview = self.propertyview)
    self.datacubeview = datacubeview.DatacubeTableView(self._cube)
    
    layout = QGridLayout()

    splitter = QSplitter(Qt.Vertical)

    splitter.addWidget(self.objectview)
    splitter.addWidget(self.propertyview)
    
    self.tabs.addTab(splitter,"Properties")
    self.tabs.addTab(self.datacubeview,"Datacube")
    
    self.tabs.setMinimumWidth(300)

    layout.addWidget(self.tabs,0,0)
    layout.addWidget(self.view,0,1)

    mainWidget = QWidget(self)
    mainWidget.setLayout(layout)

    self.setCentralWidget(mainWidget)
    
    currentItem = self._root
    
    group = objects.Group(self._root,name = "Group")

    self.view.rotate(45)
    
    for i in range(0,100):
    
#      someItem = objects.Label(self._root,name = "child",text = "Hello, world die %d-te" % i)
#      someItem.setFontSize(10,"pt")
#      someItem.setRotation(random.random()*360)
#      someItem.setY(random.random()*10,"cm")
#      someItem.setX(random.random()*10,"cm")
      
      graphicsItem = objects.Image(self._root,name = "image %d" % i)

      graphicsItem.translate(random.random()*10,random.random()*10,unit = 'cm')

      s = random.random()*2.0

      newSize = graphicsItem.size()
  
      graphicsItem.setSize(QSize(newSize.width()*s,newSize.height()*s))
      
      graphicsItem.rotate(s*360.0)
      
      graphicsItem.setOpacity(0.5)

    
    
    self._timer = QTimer(self)
    self._timer.setInterval(100)
    self._timer.start()
    
    self.connect(self._timer,SIGNAL("timeout()"),self.onTimer)
    
    
  def onTimer(self):
#    self.scene.invalidate()
    self._cube.set( x = 4,a = 5)
    self._cube.commit()

if __name__ == '__main__':
  app = QApplication(sys.argv)

  MyWindow = Editor()
  MyWindow.show()

  app.exec_()