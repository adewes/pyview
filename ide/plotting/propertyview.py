import sys
import mimetypes
import getopt
import re
import weakref

from PySide.QtGui import * 
from PySide.QtCore import *
#from pyview.lib.wikidb import *

from PySide.QtGui import * 
from PySide.QtCore import *
from objects import *

#This is our directory model...
class PropertyViewModel(QAbstractItemModel):

  def updated(self,object,property = None,value = None):
    if object != self._object:
      object.detach(self)
    else:
      self.emit(SIGNAL("layoutChanged()"))
  
  def flags(self,index):
    return QAbstractItemModel.flags(self,index) | Qt.ItemIsEditable
  
  def __init__(self,object):
    QAbstractItemModel.__init__(self)
    self.setObject(object)
    self._IDs = dict()
    self._IDs = dict()
    self._cnt = 0
  
  def setObject(self,object):
    if hasattr(self,'_object') and self._object != None:
      self._object.detach(self)
    self._object = object
    self._object.attach(self)
    
  def getIndex(self,property):
    ID = property.ID()
    if not ID in self._IDs:
      self._IDs[ID] = self._cnt
      self._cnt+=1
    return self._IDs[ID]

  def getProperty(self,index):
    for key in self._IDs.keys():
      if self._IDs[key] == int(index):
        return self._object.getPropertyByID(key)
    return None
          
  def index(self,row,column,parent):
    if parent == QModelIndex():
      return self.createIndex(row,column,self.getIndex(self._object.properties().children()[row]))
    else:
      node = self.getProperty(parent.internalId())
      if node != None:    
        if row<len(node):
         return self.createIndex(row,column,self.getIndex(node.children()[row]))
    return QModelIndex()
    
  def parent(self,index):
    if index == QModelIndex():
      return QModelIndex()
    node = self.getProperty(index.internalId())
    if node == None:
      return QModelIndex()  
    if node.parent() == None:
      return QModelIndex()
    if node.parent() == self._object.properties():
      return QModelIndex()
    if node.parent().parent() == None:
      return self.createIndex(0,0,self.getIndex(node.parent()))
    else:
      grandparent = node.parent().parent()
    if node.parent() in grandparent.children():
      row = grandparent.children().index(node.parent())
    else:
      row = None
    if row == None:
      return QModelIndex()
    return self.createIndex(row,0,self.getIndex(node.parent()))

  def headerData(self,section,orientation,role = Qt.DisplayRole):
    if role == Qt.DisplayRole and orientation == Qt.Horizontal:
      if section == 0:
        return "Name"
      elif section == 1:
        return "Value"
    return QAbstractItemModel.headerData(self,section,orientation,role)

  #Returns the data for the given node...
  def data(self,index,role):
    if role == Qt.DisplayRole:
      if index.internalId() != None:
        property = self.getProperty(index.internalId())
        if property == None:
          return "property not found!"
        else:
          if index.column() == 0:
            return property.name() 
          if index.column() == 1:
            return property.get()
    return 
    
  def hasChildren(self,index):
    return True
  
  def columnCount(self,index):
    return 2
    
  #Returns the rowCount of a given node. If the corresponding directory has never been parsed, we call buildDirectory to do so.
  def rowCount(self,index):
    if index == QModelIndex():
      return len(self._object.properties())
    node = self.getProperty(index.internalId())
    if node == None:
      return 0
    return len(node)

class PropertyDelegate(QItemDelegate):
  
  def setModel(self,model):
    self._model = model

  def sizeHint(self,option,index):
    if index.column() == 0:
      return QItemDelegate.sizeHint(self,option,index)
    property = self._model.getProperty(index.internalId())
    if hasattr(property,"sizeHint"):
      return property.sizeHint(option)    
    else:
      return QItemDelegate.sizeHint(self,option,index)
    
  def paint(self,painter,option,index):
    if index.column() == 0:
      return QItemDelegate.paint(self,painter,option,index)
    property = self._model.getProperty(index.internalId())
    if hasattr(property,"paint"):
      property.paint(painter,option)    
    else:
      return QItemDelegate.paint(self,painter,option,index)
  
  def setModelData(self,editor,model,index):
    property = self._model.getProperty(index.internalId())
    property.setModelData(editor)
  
  def setEditorData(self,editor,index):
    property = self._model.getProperty(index.internalId())
    property.setEditorData(editor)
  
  def createEditor(self,parent,option,index):
    if index.column() == 0:
      return None 
    property = self._model.getProperty(index.internalId())
    return property.createEditor(parent,option)


class PropertyTreeView(QTreeView):

  def setObject(self,object):
    self.dirModel.setObject(object)
    self.reset()
    self.expandAll()

  def __init__(self,object = None,parent = None):
    QTreeView.__init__(self,parent)
    self.delegate = PropertyDelegate(self)
    self.dirModel = PropertyViewModel(object)
    self.delegate.setModel(self.dirModel)
    self.setModel(self.dirModel)
    self.setItemDelegate(self.delegate)
    self.setAutoScroll(True)
    self.setEditTriggers(QAbstractItemView.DoubleClicked
                                 | QAbstractItemView.SelectedClicked)

    self.connect(self,SIGNAL("doubleClicked(QModelIndex)"),self.doubleClicked)

  def doubleClicked(self,index):
    pass
