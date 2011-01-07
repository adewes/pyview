
from PySide.QtGui import * 
from PySide.QtCore import *
from pyview.lib.patterns import Subject

from properties import *

import math

def dot(a,b):
  return a.x()*b.x()+a.y()*b.y()
  
def cross(a,b):
  return a.x()*b.y()-a.y()*b.x()
  
def norm(a):
  return math.sqrt(a.x()*a.x()+a.y()*a.y())
class Object(QGraphicsItem,Subject):

  """
  The base class for all objects to be drawn on the canvas.
  """

  def convertUnits(self,value,fromUnit,toUnit):
    
    if fromUnit == toUnit:
      return value
    
    if self.scene() == None:
      return None
    
    resolution = self.scene().resolution()
    
    if fromUnit != "px":
      if fromUnit == "mm":
        pixelValue = 1.0/25.4*resolution*value
      if fromUnit == "cm":
        pixelValue = 1.0/2.54*resolution*value
      if fromUnit == "inch":
        pixelValue = resolution*value
      if fromUnit == "pt":
        pixelValue = 1.0/72.0*resolution*value
    else:
      pixelValue = value 
      
    if toUnit == "px":
      return pixelValue
    elif toUnit == "mm":
      return pixelValue/resolution*25.4
    elif toUnit == "cm":
      return pixelValue/resolution*2.54
    elif toUnit == "inch":
      return pixelValue/resolution
    elif toUnit == "pt":
      return pixelValue/resolution*72
  
  def mouseDoubleClickEvent(self,e):
    self.scene().setTopLevelItem(self)
    
  def __init__(self, parent = None,name = "unnamed"):
    QGraphicsItem.__init__(self,parent)
    Subject.__init__(self)
    self._name = name    
    self.setAcceptedMouseButtons(Qt.NoButton)
    self._scaling = False
    self._rotating = False
    
    self._geometry = dict()
    self._geometry["scale_x"] = 1.0
    self._geometry["scale_y"] = 1.0
    
    self._scaleTransform = QTransform()

    self._geometry["shear_x"] = 0
    self._geometry["shear_y"] = 0
    
    self._shearTransform = QTransform()

    self._geometry["rotation"] = 0
    
    self._rotationTransform = QTransform()
    
    self._geometry["translation_x"] = 0
    self._geometry["translation_y"] = 0
    
    self._unitX = "px"
    self._unitY = "px"
    
    self._translationTransform = QTransform()
    
    self.setFlags(self.flags() | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemClipsChildrenToShape)
    self.setAcceptDrops(True)
    self._boundingRect = QRectF(-101,-101,204,204)
    self._property = Property("properties")

    position = Property("position")
    position_x = DimensionalProperty("x",parent = position,get = lambda : (self.convertUnits(self.x(),"px",self._unitX),self._unitX),set = lambda x,unit: self.setX(x,unit),converter = self.convertUnits)
    position_x = DimensionalProperty("y",parent = position,get = lambda : (self.convertUnits(self.y(),"px",self._unitY),self._unitY),set = lambda y,unit: self.setY(y,unit),converter = self.convertUnits)

    self.addProperty(position)

    scale = Property("scale")
    scale_x = FloatProperty("x",parent = scale,get = lambda : self.scale()[0],set = lambda x: self.setScale(x = x))
    scale_y = FloatProperty("y",parent = scale,get = lambda : self.scale()[1],set = lambda y: self.setScale(y = y))

    self.addProperty(scale)

    rotation = FloatProperty("rotation", get = self.rotation,set = self.setRotation)
    
    self.addProperty(rotation)
  
  def translate(self,x,y,unit = "px"):
    self.setX(x,unit)
    self.setY(y,unit)
  
  def setX(self,x,unitX = "px"):
    self._unitX = unitX
    self.setPos(self.convertUnits(x,unitX,"px"),self.y())

  def setY(self,y,unitY = "px"):
    self._unitY = unitY
    self.setPos(self.x(),self.convertUnits(y,unitY,"px"))
    
  def setSize(self,size):
  
    sx = size.width()
    sy = size.height()
    
    if sx == None:
      sx = self.boundingRect().width()
      
    if sy == None:
      sy = self.boundingRect().height()
  
    anchor = self.boundingRect().topLeft()
  
    rect = QRectF(anchor,QSizeF(max(0,sx),max(0,sy)))
    self._boundingRect = rect
    
    self.prepareGeometryChange()
    
  def size(self):
    return QSize(self.boundingRect().width(),self.boundingRect().height())
  
  def setScale(self,x = None,y = None):

    if x != None:
      self._geometry["scale_x"] = x
    if y != None:
      self._geometry["scale_y"] = y
    
    self._scaleTransform = QTransform()
    self._scaleTransform.scale(self._geometry["scale_x"],self._geometry["scale_y"])
    
    self.updateTransform()
    
  def scale(self):
    return (self._geometry["scale_x"],self._geometry["scale_y"])

  def rotate(self,angle):
    return self.setRotation(math.fmod(angle,360))

  def setRotation(self,angle):
    self._geometry["rotation"] = math.fmod(angle,360)

    self._rotationTransform = QTransform()
    self._rotationTransform.rotate(angle)

    self.updateTransform()
        
  def updateTransform(self):
    translation = QTransform()
    center = self.transformOriginPoint()
    
    centerMapped = self.transform().map(center)

    centerTranslation = QTransform()
    centerTranslation.translate(-center.x(),-center.y())


    newCenter = (centerTranslation*self._scaleTransform*self._shearTransform*self._rotationTransform*centerTranslation.inverted()[0]).map(center)

    #The center coordinate should fall on the same scene coordinate before and after the transformation. We translate to make sure this is the case.

    d = newCenter-centerMapped
    
    translation.translate(-d.x(),-d.y())
    
    self._translationTransform = translation
    
    transform = centerTranslation*self._scaleTransform*self._shearTransform*self._rotationTransform*centerTranslation.inverted()[0]*self._translationTransform
    self.setTransform(transform)
    self.notify("updateTransform",transform)
    
  def rotation(self):
    return self._geometry["rotation"]
  
  def ungrabMouse(self):
    QGraphicsItem.ungrabMouse(self)
      
  def addProperty(self,property):
    property.setObject(self)
    self._property.addChild(property)
    
  def parent(self):
    return self.parentItem()
    
  def properties(self):
    return self._property
    
  def __len__(self):
    return len(self._children)
    
  def getPropertyByID(self,ID):
    names = ID.split(":")
    currentProperty = self._property
    if len(names) == 1:
      return currentProperty
    names.pop(0)
    while len(names)>0:
      name = names.pop(0)
      currentProperty = currentProperty.getChild(name)
      if currentProperty == None:
        return None
    return currentProperty
    
  def name(self):
    return self._name
    
  def len(self):
    return len(self.childItems())
          
  def boundingRect(self):
    return self._boundingRect
  
  def getXY(self):
    origin = self.mapToParent(self.mapFromScene(QPointF(0,0)))
    x = self.mapToParent(self.mapFromScene(QPointF(1,0)))-origin
    y = self.mapToParent(self.mapFromScene(QPointF(0,1)))-origin
    x /= norm(x)
    y /= norm(y)
    return (x,y)
        
  def mousePressEvent(self,e):
    
    view = self.scene().views()[0]

    polygon = self.mapToScene(self.boundingRect())

    rotateCirclePos = view.mapFromScene(self.mapToScene(self.boundingRect().center()-QPointF(0,self.boundingRect().height()/2)))
    
    if (view.mapFromScene(e.scenePos())-rotateCirclePos).manhattanLength() < 10:
      self._rotating = True
      e.accept()
      self._currentPos = e.scenePos()
      self._startPoint = e.scenePos()
      self._centerPoint = self.mapToScene(self.transformOriginPoint())
      self._centerPointItem = self.transformOriginPoint()
      self._startVector = self._startPoint-self._centerPoint
      self._startVector /= norm(self._startVector)
      self._startAngle = self.rotation()

    for i in range(0,polygon.size()):
      corner = view.mapFromScene(polygon.at(i))
      if (view.mapFromScene(e.scenePos())-corner).manhattanLength() < 10:
        self._scaling = True
        self._scalingIndex = i
        self._size = self.size()
        self._fixedPoint = polygon.at((i+2)%4)
        self._fixedPointFunction = lambda i = i: self.mapToScene(QPolygonF(self.boundingRect()).at((i+2)%4))
        self._fixedPointItem = lambda : QPolygonF(self.boundingRect()).at((i+2)%4)
        self._startPoint = polygon.at(i)

        origin = polygon.at(0)*100

        self._scaleX = polygon.at(1)*100-origin
        self._scaleY = polygon.at(3)*100-origin
  
        self._scaleX/= norm(self._scaleX)
        self._scaleY/= norm(self._scaleY)
        
        self._diff = self._startPoint - self._fixedPoint
        self._startTransform = self.transform()
        e.accept()
    QGraphicsItem.mousePressEvent(self,e)
    
  def mouseReleaseEvent(self,e):
    self._scaling = False
    self._rotating = False
    QGraphicsItem.mouseReleaseEvent(self,e)
    
  def mouseMoveEvent(self,e):
    
    if self._rotating:
      
      newVector = e.scenePos() - self._centerPoint
      newVector /= norm(newVector)
      
      self._currentPos = e.scenePos()

      z = QPointF(self._startVector.y(),-self._startVector.x())
        
      angle = math.atan2(dot(newVector,self._startVector),dot(newVector,z))*180/math.pi-90
      
      (x,y) = self.getXY()
      
      if cross(x,y) < 0:
        angle = -angle
      
      self.setRotation(self._startAngle+angle)      

    if self._scaling:

      diff = e.scenePos()-self._fixedPoint
      
      xy = dot(self._scaleX,self._scaleY)

      dx = dot(diff,self._scaleX)
      dy = dot(diff,self._scaleY)
      
      diff_x = (dx - dy*xy)/(1-xy)
      diff_y = (dy - dx*xy)/(1-xy)
            
      
      sdx = dot(self._diff,self._scaleX)
      sdy = dot(self._diff,self._scaleY)

      start_diff_x = (sdx - sdy*xy)/(1-xy)
      start_diff_y = (sdy - sdx*xy)/(1-xy)


      oldFixedPointItem = self._fixedPointFunction()
  
      sx = diff_x/start_diff_x*self._size.width()
      sy = diff_y/start_diff_y*self._size.height()
      
      if sx == 0:
        sx = 0.001

      if sy == 0:
        sy = 0.001

      self.setSize(QSize(sx,sy))

      newFixedPointItem = self._fixedPointFunction()
            
      d = newFixedPointItem-oldFixedPointItem
      
      self.moveBy(-d.x(),-d.y())
      
      self.notify("scaled")

    QGraphicsItem.mouseMoveEvent(self,e)
    
  def paintManipulators(self,painter,view):
    if self._rotating:
      start = view.mapFromScene(self.mapToScene(self.transformOriginPoint()))
      end = view.mapFromScene(self._currentPos)
      painter.drawLine(start,end)
    if self.isSelected():
      x = self.boundingRect().topRight()-self.boundingRect().topLeft()
      if not self._rotating:
        painter.drawEllipse(view.mapFromScene(self.mapToScene(self.boundingRect().center()-QPointF(0,self.boundingRect().height()/2))),10,10)
      polygon = view.mapFromScene(self.mapToScene(self.boundingRect()))
      for i in range(0,polygon.size()):
        p = polygon.at(i)
        painter.drawRect(int(p.x())-5,int(p.y())-5,10,10)
    
  def paint(self,painter,option,widget = None ):
    pass
    
class Group(Object):
  
  def __init__(self,parent = None,name = None):
    Object.__init__(self,parent = parent,name = name)
    
  def boundingRect(self):
    return self.childrenBoundingRect()

class Root(Object):

  def __init__(self,parent = None,name = None):
    Object.__init__(self,parent = parent,name = name)
    self.setFlags(QGraphicsItem.ItemHasNoContents)
  
  def boundingRect(self):
    return QRectF()

class Curve(Object):

  def __init__(self,parent = None,name = "unnamed"):
    Object.__init__(self,parent = parent,name = name)
    self._points = []
    
    for i in range(0,10000):
      self._points.append(QPointF(float(i)/100.0,100*math.sin(float(i)*0.01)))
      
  def paint(self,painter,option,widget = None):
    
    painter.setRenderHints(QPainter.Antialiasing)
    
class LineEditor(QGraphicsProxyWidget):

  def __init__(self,parent = None,name = "unnamed"):
    QGraphicsProxyWidget.__init__(self,parent = parent)
    self.edit = QLineEdit("10")
    self.setWidget(self.edit)

  def name(self):
    return "test"
    
  def __attribute__(self,name):
    return Object.__attribute__(name)
    
            
    painter.drawLines(self._points)            

class Line(Object):

    
  def __init__(self,parent,name):
    Object.__init__(self,parent,name)

    resolution = self.scene().resolution()

    self._radius = 5.0/2.54*resolution
    self._width = 1.0/2.54*resolution
    
  def boundingRect(self):
    return QRectF(-self._radius/2-self._width/2,-self._radius/2-self._width/2,self._radius+self._width,self._radius+self._width)
    
  def paint(self,painter,option,widget = None):
    
    pen = QPen()
    
    pen.setWidth(self._width)

    painter.setPen(pen)
      
    painter.drawEllipse(-self._radius/2,-self._radius/2,self._radius,self._radius)
    
class Image(Object):

  def __init__(self,parent = None,name = "unnamed"):
    Object.__init__(self,parent,name)
    self._image = QPixmap("ich_1.jpg")
    self._scaledImage = self._image.copy()
    self.setTransformOriginPoint(QRectF(self._scaledImage.rect()).center())
    
    
  def rescaleImage(self,size):
    self._scaledImage = self._image.scaled(size)
    self.setTransformOriginPoint(QRectF(self._scaledImage.rect()).center())

  def paint(self,painter,option,widget = None):
    painter.drawPixmap(QRectF(self._scaledImage.rect()),self._scaledImage,QRectF(self._scaledImage.rect()))
    
  def boundingRect(self):
    return QRectF(self._scaledImage.rect())

  def setSize(self,size):
    """
    When the size of the text box is changed we make sure that it doesn't become too small...
    """
    Object.setSize(self,size)
    self.rescaleImage(size)
    

class Label(Object):

  def boundingRect(self):
    return self._boundingRect
       
  def fontSize(self):
    return (self._fontSize,self._fontSizeUnit)
    
  def setSize(self,size):
    """
    When the size of the text box is changed we make sure that it doesn't become too small...
    """
    Object.setSize(self,size)
    if self.boundingRect().width() < self._minimumBoundingRect.width():
      self.boundingRect().setWidth(self._minimumBoundingRect.width())
    if self.boundingRect().height() < self._minimumBoundingRect.height():
      self.boundingRect().setHeight(self._minimumBoundingRect.height())
    
    
  def setFontSize(self,value,unit = "px"):
    numericValue = float(value)
    pixelSize = self.convertUnits(numericValue,str(unit),"px")
    self._font.setPixelSize(pixelSize*abs(self._scalingFactor))
    self._fontSize = numericValue
    self._fontSizeUnit = unit
    self.updateBoundingRect()
  
  def updateBoundingRect(self):
    fontMetrics = QFontMetrics(self._font)
    self._minimumBoundingRect = QRectF(fontMetrics.boundingRect(self._text))
    self._boundingRect = self._minimumBoundingRect
    self.prepareGeometryChange()
    self.setTransformOriginPoint(self.boundingRect().center())
                
    
  def __init__(self,parent = None,name = "unnamed",text = "100 pt"):
    Object.__init__(self,parent = parent,name = name)
    self._text = text
    self._font = QFont("Times New Roman")
    self._scalingFactor = 1
    self.setFontSize(240,"px")
    fontSize = DimensionalProperty(name = "font size",get = self.fontSize,set = self.setFontSize,converter = self.convertUnits)
    self.addProperty(fontSize)
    
  def paint(self,painter,option,widget = None):

#    painter.setRenderHint(QPainter.Antialiasing)
      
    painter.setFont(self._font)
    painter.drawText(self._boundingRect,Qt.AlignLeft,self._text)
