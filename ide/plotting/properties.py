from PySide.QtGui import * 
from PySide.QtCore import *

class Property:
  
  def __init__(self,name,object = None,parent = None,get = None,set = None):
    self._name = name
    self._object = object
    self._children = []
    self.setParent(parent)
    self._set = set
    self._get = get
    
  def get(self):
    if self._get == None:
      return None
    return self._get()
    
  def set(self,*args,**kwargs):
    if self._set == None:
      return False
    return self._set(*args,**kwargs)

  def setParent(self,parent):
    self._parent = parent
    if parent != None:
      parent.addChild(self)
    
  def addChild(self,property):
    if not property in self._children:
      self._children.append(property)
      property.setParent(self)
  
  def children(self):
    return self._children
    
  def name(self):
    return self._name
    
  def __len__(self):
    return len(self._children)
    
  def parent(self):
    return self._parent
  
  def getChild(self,name):
    for child in self._children:
      if child.name() == name:
        return child
    return None
    
  def ID(self):
    if self._parent != None:
      return self._parent.ID()+":"+self._name
    else:
      return self._name
    
  def setObject(self,object):
    self._object = object
    for child in self._children:
      child.setObject(object)
      
  def createEditor(self,parent,option = None):
    return None
    
  def setEditorData(self,editor):
    pass
    
  def setModelData(self,editor):
    pass
    
      
class FloatProperty(Property):
  
  def __init__(self,name,object = None,parent = None,get = None,set = None):
    Property.__init__(self,name,object,parent,get,set)

  def createEditor(self,parent,option = None):
    return QLineEdit(parent)
    
  def setEditorData(self,editor):
    print editor.width()
    print editor.height()
    editor.setText(str(self.get()))
    
  def setModelData(self,editor):
    value = float(editor.text())
    self.set(value)
    
class DimensionalProperty(FloatProperty):
  
  def __init__(self,name,object = None,parent = None,dimensions = ["mm","cm","inch","pt","px"],converter = None,get = None,set = None):
    FloatProperty.__init__(self,name,object,parent,get,set)
    self._dimensions = dimensions
    self._converter = converter
    
  def dimensions(self):
    return self._dimensions

  class EditorWidget(QFrame):
  
    def sizeHint(self):
      return QSize(200,20)
      
    def setUnit(self,unit):
      print "Changing unit from %s to %s" % (str(self._unit),unit)
      if self._unit != None and self._converter != None:
        self.setValue(self._converter(self._value,str(self._unit),str(unit)))
      self._unit = unit
      self._dimensionEdit.setCurrentIndex(self._dimensionEdit.findText(unit))         
      
    def setValue(self,value):
      self._value = value
      self._textEdit.setText(str(value))
      
    def __init__(self,property,parent = None,converter = None):
      QFrame.__init__(self,parent = parent)
      self.setAutoFillBackground(True)
      self.setContentsMargins(0,0,0,0)
      self._unit = None
      self._converter = converter
      self._value = None
      self._layout = QBoxLayout(QBoxLayout.LeftToRight)
      self._layout.setContentsMargins(0,0,0,0)
      self._textEdit = QLineEdit(self)
      self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
      self._dimensionEdit = QComboBox(self)
      (value,valueDimension) = property.get()
      for dimension in property.dimensions():
        self._dimensionEdit.addItem(dimension)
      self._layout.addWidget(self._textEdit)
      self._layout.addWidget(self._dimensionEdit)
      self.setFocusProxy(self._textEdit)
      self.setLayout(self._layout)
      self.connect(self._dimensionEdit,SIGNAL("currentIndexChanged(const QString&)"),self.setUnit)
      
      
  def sizeHint(self,option):
    self._fontMetrics = QFontMetrics(option.font)
    return self._fontMetrics.size(Qt.TextSingleLine,"test")
      
  def paint(self,painter,option):
    painter.save()
    painter.setFont(option.font)
    if option.state & QStyle.State_Selected:
      painter.fillRect(option.rect, option.palette.highlight())
      painter.setBrush(option.palette.highlightedText())
    (value,unit) = self.get()
    painter.drawText(option.rect.bottomLeft()-QPoint(-1,1),"%g %s" % (value,unit))
    painter.restore()

  def createEditor(self,parent,option = None):
    widget = self.EditorWidget(self,parent = parent,converter = self._converter)
    return widget
    
  def setEditorData(self,editor):
    (value,unit) = self.get()
    editor.setValue(value)
    editor.setUnit(unit)
    
  def setModelData(self,editor):
    value = float(editor._textEdit.text())
    unit = editor._dimensionEdit.currentText()
    self.set(value,unit)

