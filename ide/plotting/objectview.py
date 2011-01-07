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

#This is our directory model...
class ObjectViewModel(QAbstractItemModel):
  
  def __init__(self,root):
    QAbstractItemModel.__init__(self)
    self.root = root
    self._indices = dict()
    
    
  def getIndex(self,object):
    r = self.ref(object)
    ir = id(r)
    self._indices[ir] = r
    return ir

  def getObject(self,index):
    if index in self._indices:
      return self._indices[index]()
  
  def ref(self,object):
    return weakref.ref(object)
        
  def index(self,row,column,parent):
    if parent == QModelIndex():
      return self.createIndex(row,column,self.getIndex(self.root))
    else:
      node = self.getObject(parent.internalId())
      if node != None:    
        if row<node.len():
         return self.createIndex(row,column,self.getIndex(node.childItems()[row]))
    return QModelIndex()
    
  def parent(self,index):
    if index == QModelIndex():
      return QModelIndex()
    node = self.getObject(index.internalId())
    if node == None:
      return QModelIndex()  
    if node.parent() == None:
      return QModelIndex()
    if node.parent().parent() == None:
      return self.createIndex(0,0,self.getIndex(self.root))
    else:
      grandparent = node.parent().parent()
    if node.parent() in grandparent.childItems():
      row = grandparent.childItems().index(node.parent())
    else:
      row = None
    if row == None:
      return QModelIndex()
    return self.createIndex(row,0,self.getIndex(node.parent()))

  #Returns the data for the given node...
  def data(self,index,role):
    if role == Qt.DisplayRole:
      if index.internalId() != None:
        object = self.getObject(index.internalId())
        if object == None:
          return ""
        else:
          return object.name() 
    elif role == Qt.DecorationRole:
      pass
    return None
    
  def hasChildren(self,index):
    return True
  
  def columnCount(self,index):
    return 1
    
  #Returns the rowCount of a given node. If the corresponding directory has never been parsed, we call buildDirectory to do so.
  def rowCount(self,index):
    if index == QModelIndex():
      return 1
    node = self.getObject(index.internalId())
    if node == None:
      return 0
    return node.len()

class ObjectTreeView(QTreeView):

  def selectionChanged(self,selected,deselected):
    if len(selected.indexes())==0:
      return
    object = self.dirModel.getObject(selected.indexes()[0].internalId())
    if self._propertyview != None and object != None:
      self._propertyview.setObject(object)

  def __init__(self,root,parent = None,propertyview = None):
    QTreeView.__init__(self,parent)
    self._propertyview = propertyview
    self.dirModel = ObjectViewModel(root)
    self.setModel(self.dirModel)
    self.setAutoScroll(True)
    self.connect(self,SIGNAL("doubleClicked(QModelIndex)"),self.doubleClicked)

  def doubleClicked(self,index):
    pass
