import sys
import mimetypes
import getopt
import re

from PySide.QtGui import * 
from PySide.QtCore import *
#from pyview.lib.wikidb import *

from PySide.QtGui import * 
from PySide.QtCore import *

#This is our directory model...
class ArticleModel(QAbstractItemModel):
  
  def __init__(self):
    QAbstractItemModel.__init__(self)
    self.root = ArticleRoot()
        

  def index(self,row,column,parent):
    if parent == QModelIndex():
      return self.createIndex(row,column,self.root.childAtRow(row).id)
    else:
      node = Article.get(parent.internalId())
      if node != None:    
        if row<node.len():
         return self.createIndex(row,column,node.childAtRow(row).id)
    return QModelIndex()
    
  def parent(self,index):
    if index == QModelIndex():
      return QModelIndex()
    node = Article.get(index.internalId())
    if node == None:
      return QModelIndex()  
    if node.parent == None:
      return QModelIndex()
    if node.parent.parent == None:
      grandparent = self.root
    else:
      grandparent = node.parent.parent
    row = grandparent.rowOfChild(node.parent.id)
    if row == None:
      return QModelIndex()
    return self.createIndex(row,0,node.parent.id)

  #Returns the data for the given node...
  def data(self,index,role):
    if role == Qt.DisplayRole:
      if index.internalId() != None:
        article = Article.get(index.internalId())
        if article == None:
          return ""
        if article.parent != None:
          parentID = article.parent.id
        else:
          parentID = 0
        revisions = article.revisions.orderBy("revision desc")
        if revisions != None and revisions.count()>0:
          latestRevision = revisions[0]    
          if latestRevision != None:
            return "%s, Rev:%d" %(latestRevision.title,latestRevision.revision)
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
      return self.root.len()
    node = Article.get(index.internalId())
    if node == None:
      return 0
    return node.len()

class ArticleTreeView(QTreeView):

  def __init__(self,fileBrowser = None,parent = None):
    QTreeView.__init__(self,parent)
    self.dirModel = ArticleModel()
    self.setModel(self.dirModel)    
    self.setAutoScroll(True)
    self.connect(self,SIGNAL("doubleClicked(QModelIndex)"),self.doubleClicked)

  def doubleClicked(self,index):
    article = Article.get(index.internalId())
    self.emit(SIGNAL("openArticle(Article)"),article)
