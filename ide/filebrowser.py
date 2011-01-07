import sys
import mimetypes

from PySide.QtGui import * 
from PySide.QtCore import *
from preferences import *


import sys
import getopt
import re

import os
import os.path
import time

from ctypes import windll
import string

from threading import Thread
import time

from PySide.QtGui import * 
from PySide.QtCore import *

cnt = 0
ID=0


#Baseclass for file and directory nodes.
class Node:
  
  def __init__(self):
    global ID
    self.ID = ID
    self.icon = None
    self.children = []
    self._parent = None
    ID+=1

  def sortByName(self,a,b):
    if a.__class__.__name__ == "DirectoryNode" and b.__class__.__name__ == "FileNode":
      return -1
    elif a.__class__.__name__ == "FileNode" and b.__class__.__name__ == "DirectoryNode":
      return 1
    ar = [(a.name(),a),(b.name(),b)]
    ar.sort()
    if ar[0][1] == a:
      return 1
    return -1

  def name(self):
    return ""
    
  def findNode(self,name):
    for child in self.children:
      if child.name().lower() == name.lower():
        return child
    return None
    
  def parent(self):
    return self._parent
    
  def setParent(self,parent):
    self._parent = parent
    
  def addChild(self,node):
    node.setParent(self)
    self.children.append(node)

  def sortNodes(self,nodes,function):
    return sorted(nodes,function)
        
  def len(self):
    return len(self.children)
    
  def rowOfChild(self,child):
    for i in range(0,len(self.children)):
      if child == self.children[i]:
        return i
    return None
    
  def childAtRow(self,row):
    if row<len(self.children):
      return self.children[row]
    return None
    
  def hasChildren(self):
    if len(self.children) > 0:
      return True
    return False
    
class InfoNode(Node):
  
  def __init__(self,info):
    Node.__init__(self)
    self.info = info
    
  def name(self):
    return self.info
  

#Returns a list of all available drives on the OS.
def get_drives():
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.uppercase:
        if bitmask & 1:
            drives.append(letter+":\\")
        bitmask >>= 1

    return drives

class DirectoryThread(Thread):

  def __init__(self,node,item):
    Thread.__init__(self)
    self._stop = False
    self.node = node
    self.item = item
    self.directoryNodes = 0
    self.nodes = []
    
  def stop(self):
    self._stop = True
    
  def run(self):
    try:
      self.nodes = self.node.parseDirectory()
      for node in self.nodes:
        if node.__class__.__name__ == "DirectoryNode":
          self.directoryNodes+=1
    except:
      print "Error: Could not parse directory \"%s\"" % self.node.fullPath()

#The directory node class
class DirectoryNode(Node):

  provider = None

  def __init__(self,directory,base = "",specialPath = None):
    Node.__init__(self)
    self.base = base
    self.garbage = []
    self.fileChildren = []
    self.isBuilding = False
    self.hasNewData = False
    self.checked = False
    self.specialPath = None
    self.directory = directory  
    if self.base == "":
      self._fullPath = os.path.normcase(os.path.normpath(self.directory))
    else:
      self._fullPath = os.path.normcase(os.path.normpath(self.base + "\\" + self.directory))    
    FileInfo = QFileInfo(self.fullPath())
    if DirectoryNode.provider == None:
      DirectoryNode.provider = QFileIconProvider()
    self.icon = QFileIconProvider.icon(DirectoryNode.provider,FileInfo)
    self.mTime = 0
    
  def addChild(self,node):
    node.setParent(self)
    if node.__class__.__name__ == "FileNode":
      self.fileChildren.append(node)
    else:
      self.children.append(node)
  
  #Recursively searchs for a given file path in the node hirarchy      
  def searchPath(self,path, expandNodes = False):
    normpath = os.path.normcase(os.path.normpath(path))
    if normpath == self.fullPath():
      return self
    if self.fullPath() != "":
      if re.search(r'\\$',self.fullPath()):
        match = re.match(re.escape(self.fullPath()),normpath)
      else:
        match = re.match(re.escape(self.fullPath())+r'\\',normpath)
      if match == None:
        return None
      prefix = self.fullPath()
    else:
      prefix = ""
    if (not self.isChecked()) and expandNodes == True:
      nodes = self.parseDirectory() 
      for node in nodes:
        self.addChild(node)
      self.checked = True
    nodes = self.children
    if nodes == None:
      return self
    for node in nodes:
      if node.__class__.__name__ == "DirectoryNode":
        result = node.searchPath(normpath,expandNodes)
        if result != None:
          return result
    return self
        
  def name(self):
    return self.directory

  def fullPath(self):
    if self.specialPath != None:
      return self.specialPath
    return self._fullPath
    
  def isChecked(self):
    return self.checked
             
  #Parses the node's directory and returns all subdirectories and files in a list. 
  def parseDirectory(self):
    if self.fullPath() == "":
      self.checked = True
      return
    nodes = []
    statinfo = os.stat(self.fullPath())
    self.mTime = statinfo.st_mtime
    files = os.listdir(self.fullPath())
    for filename in files:
      if os.path.isdir(self.fullPath()+"\\"+filename):
        dirNode = DirectoryNode(filename,self.fullPath())
        nodes.append(dirNode)
      else:
        fileNode = FileNode(filename,self.fullPath())
        nodes.append(fileNode)
    return nodes#self.sortNodes(nodes,self.sortByName)
    
class SpecialNode(DirectoryNode):
  
  def __init__(self,path,text):
    DirectoryNode.__init__(self,path,"")
    self.text = text
    
  def fullPath(self):
    return self.directory
    
  def isChecked(self):
    return True
    
  def name(self):
    return self.text
    
#The file node class
class FileNode(Node):

  def hasChildren(self):
    return False
    
  def name(self):
    return self.filename
    
  def fullPath(self):
    if self.base == "":
      return self.filename
    return os.path.normpath(self.base + "\\" + self.filename)

  def __init__(self,filename,base  = ""):
    Node.__init__(self)
    self.filename = filename
    self.base = base
    FileInfo = QFileInfo(self.fullPath())
    if DirectoryNode.provider == None:
      DirectoryNode.provider = QFileIconProvider()
    self.icon = QFileIconProvider.icon(DirectoryNode.provider,FileInfo)
  
#This is our directory model...
class MyDirModel(QAbstractItemModel):
  
  def __init__(self):
    QAbstractItemModel.__init__(self)
    self.garbage = []
    self.timer = QTimer(self)
    self.timer.setInterval(400)
    self.connect(self.timer,SIGNAL("timeout()"),self.onTimer)
    self.timer.start()
    self.setup()
    self.buildThreads = []
    self.activeThread = None
    
  #This function gets called periodically and checks if there are any queued or finished directory threads waiting to be processed...
  def onTimer(self):
    if self.activeThread == None:
      if len(self.buildThreads)>0:
        self.activeThread = self.buildThreads.pop()
        self.activeThread.start()
        return
    elif self.activeThread.isAlive() == False:
      thread = self.activeThread
      self.activeThread = None
      if thread.item.isValid() == False:
        return
      parent = thread.item.parent()
      if parent != QModelIndex() or True:
        index = self.index (thread.item.row(),thread.item.column(),parent)
        if index != QModelIndex():
          thread.node.fileChildren = []
          if thread.node.len()>0:
            self.removeRows(0,thread.node.len(),index)
          self.beginInsertRows(index,0,thread.directoryNodes-1)
          thread.node.fileChildren = []
          for node in thread.nodes:
            thread.node.addChild(node)
          thread.node.checked = True
          self.endInsertRows()
        self.emit(SIGNAL("nodeUpdated(QVariant)"),thread.node)
    
  def setup(self):
    self.root = SpecialNode("","[root]")
    drives = get_drives()
    for drive in drives:
      Drive = DirectoryNode(drive)
      self.root.addChild(Drive)
      
  #Creates a new build thread and queues it.
  def createBuildThread(self,item,node):
    for thread in self.buildThreads:
      if thread.node == node:
        return
    BuildThread = DirectoryThread(node,QPersistentModelIndex(item))
    self.buildThreads.append(BuildThread)
    if item.isValid() == False:
      return
    parent = item.parent()
    if parent != QModelIndex():
      index = self.index(item.row(),item.column(),parent)          
      if node.len()>0:
        self.removeRows(0,node.len(),index)
      self.beginInsertRows(index,0,0)
      infoNode = InfoNode("[please wait, loading...]")
      node.addChild(infoNode)
      self.endInsertRows()
    

  #Refreshse a given directory node...
  #Call this function only from the main thread!!!
  def refreshDirectory(self,item):
    if not item.isValid():
      return
    node = item.internalPointer()
    if node == None:
      return
    statinfo = os.stat(node.fullPath())
    if statinfo.st_mtime>node.mTime:
      self.createBuildThread(item,node)
      
  def buildDirectory(self,item):
    if not item.isValid():
      return
    node = item.internalPointer()
    if node == None:
      return
    node.checked = True
    self.createBuildThread(item,node)

  def setRoot(self,path):
    self.removeRows(0,self.rowCount(QModelIndex()),QModelIndex())
    oldroot = self.root
    self.root = SpecialNode("","[root]")
    if path == "":
      self.setup()
      return
    Directory = DirectoryNode(path)
    self.root = Directory 
    

  def index(self,row,column,parent):
    if parent == QModelIndex():
      return self.createIndex(row,column,self.root.childAtRow(row))
    else:
      node = parent.internalPointer()   
      if row<node.len():
        return self.createIndex(row,column,node.childAtRow(row))
    return QModelIndex()
    
  def parent(self,index):
    if index == QModelIndex():
      return QModelIndex()
    node = index.internalPointer()
    if node == None:
      return QModelIndex()  
    if node.parent() == None:
      return QModelIndex()
    if node.parent().parent() == None:
      return QModelIndex()
    row = node.parent().parent().rowOfChild(node.parent())
    if row == None:
      return QModelIndex()
    return self.createIndex(row,0,node.parent())

  def directoryParsed(self,thread):
    pass
    
  def headerData(self,section,orientation,role = Qt.DisplayRole):
    if role == Qt.DisplayRole and orientation == Qt.Horizontal:
      if section == 0:
        return "Directory"
    return QAbstractItemModel.headerData(self,section,orientation,role)
    
  #Returns the data for the given node...
  def data(self,index,role):
    if role == Qt.DisplayRole:
      if index.internalPointer() != None:
        return index.internalPointer().name() 
    elif role == Qt.DecorationRole:
      if index.internalPointer() != None:
        return index.internalPointer().icon
    return None
    
  def hasChildren(self,index):
    if index!= QModelIndex():
      node = index.internalPointer()
      if node.__class__.__name__ == "DirectoryNode":
        if node.checked == True and node.len() == 0:
          return False
        return True
      return False
    return True
  
  def columnCount(self,index):
    return 1
    
  #This removes "count" children of "parent" from the model, starting in row "row". The models are simultaneously removed from the view.
  #IMPORTANT: Call this function ONLY from the main thread!!!
  def removeRows(self,row,count,parent):
    self.beginRemoveRows(parent,row,row+count)
    if parent == QModelIndex(): 
      node = self.root
    else:
      node = parent.internalPointer()
    for i in range(row,row+count):
      if row<node.len():
        del node.children[row]
    self.endRemoveRows()
    
  #Returns the rowCount of a given node. If the corresponding directory has never been parsed, we call buildDirectory to do so.
  def rowCount(self,index):
    if index == QModelIndex():
      return self.root.len()
    node = index.internalPointer()
    if node.__class__.__name__ == "DirectoryNode":
      if node.isChecked() == False:
        self.buildDirectory(index)
    return node.len()

import copy

class DirectoryTreeView(QTreeView):

  #This is a bit complicated since we have to manipulate the node tree and update the tree view afterwards...
  #TO DO: Outsource this into a seperate thread...
  def changeDirectory(self,directory,inBackground = True):
    if inBackground:
      root = self.dirModel.root
      rootCopy = DirectoryNode(root.directory,root.base)
      if root == None:
        return
      foundNode = root.searchPath(directory,False)
      if foundNode == None:
        return False
      if foundNode.fullPath() != os.path.normpath(directory):
        childCopy = DirectoryNode(foundNode.directory,foundNode.base)
        result = childCopy.searchPath(directory,True)
      else:
        childCopy = foundNode
        result = foundNode
      if result != None:
        #We replace the old directory model by the new one...
        node = result
        
        #We traverse from the resulting node up the node tree to get the original node back...
        while node != childCopy and node != None:
          node = node.parent()
          #We save all the nodes on the path in order to be able to expand their corresponding views later...

        parent = foundNode.parent()
        indexOfParent = self.dirModel.createIndex(parent.rowOfChild(foundNode),0,foundNode)
        row = parent.rowOfChild(foundNode)
        #We replace the old entry...
        if foundNode != childCopy:
          self.dirModel.removeRows(0,foundNode.len(),indexOfParent)
          foundNode.fileChildren = []
          self.dirModel.beginInsertRows(indexOfParent,0,childCopy.len()-1)
          for child in childCopy.children:
            foundNode.addChild(child)
          self.dirModel.endInsertRows()
          foundNode.mTime = childCopy.mTime
          foundNode.checked = True

        #Now we expand all the nodes down to the new directory...
        self.expandAndSelectNode(result)

        return True
      return False
    else:
      pass  

  #Expands the node tree up to a given node and selects this node afterwards...
  def expandAndSelectNode(self,node):
    nodePath = []
    self.clearSelection()
    while node.parent() != QModelIndex():
      nodePath.append(node)
      node = node.parent()
    nodePath.append(node)
    parentNode = nodePath.pop()
    while len(nodePath)>0:
      currentNode = nodePath.pop()
      if parentNode.rowOfChild(currentNode) == None:
        return
      index = self.dirModel.createIndex(parentNode.rowOfChild(currentNode),0,currentNode)
      self.setExpanded(index,True)
      if len(nodePath) == 0:
        self.setSelection(self.visualRect(index),QItemSelectionModel.Select)
        self.scrollTo(index)
      parentNode = currentNode
     
  def directory(self):
    return self._directory
    
  def nodeUpdated(self,node):
    if self._fileBrowser.node() != None:
      if self._fileBrowser.node().fullPath() == node.fullPath():
        self._fileBrowser.setDirectory(node) 

  def __init__(self,fileBrowser = None,parent = None):
    QTreeView.__init__(self,parent)
    self.dirModel = MyDirModel()
    self._fileBrowser = fileBrowser
    self.setModel(self.dirModel)    
    self.connect(self,SIGNAL("collapsed(QModelIndex)"),self.itemCollapsed)
    self.connect(self,SIGNAL("doubleClicked(QModelIndex)"),self.doubleClicked)
    self.connect(self.dirModel,SIGNAL("nodeUpdated(PyQt_PyObject)"),self.nodeUpdated)
    self._directory = ""
    self.setAutoScroll(True)
    
    
  def doubleClicked(self,index):
    node = index.internalPointer()
    if node != None:
      if node.__class__.__name__ == "FileNode":
        self.emit(SIGNAL("openFile(QString)"),node.fullPath())
      
    
  def selectionChanged(self,selected,deselected):
    if len(selected) == 0:
      return
    item = selected[0]
    if len(item.indexes()) == 0:
      return
    index = item.indexes()[0]
    if index.isValid() == False:
      return
    node = index.internalPointer()
    if node == None:
      return
    if node.__class__.__name__ == "DirectoryNode":
      self._directory = node.fullPath()
      self._fileBrowser.setDirectory(node)
      self.model().refreshDirectory(index)
      
  def itemCollapsed(self,item):
    node = item.internalPointer()
    if node != None:
      self.model().refreshDirectory(item)

#This is the file browser...

    
class FileItem(QListWidgetItem):
  
  def path(self):
    return self._path

  def __init__(self,node,text = None):
    QListWidgetItem.__init__(self)
    self._path = node.fullPath()
    self._baseName = os.path.basename(node.fullPath()) 
    
    self.setText(self._baseName)
    self.setIcon(node.icon)
    
class DirectoryItem(QListWidgetItem):

  provider = None
  
  def path(self):
    return self._path

  def __init__(self,node):
    QListWidgetItem.__init__(self)
    self._path = node.fullPath()
    self._baseName = os.path.basename(node.fullPath()) 
    self.setText(self._baseName)
    self.setIcon(node.icon)
       
class FileBrowser(QListWidget):

  def directory(self):
      return self._node.fullPath()
      
  def node(self):
    return self._node

  def setDirectory(self,node):
    self._node = node
    self.clear()
    UpperDirectory = DirectoryNode(node.fullPath()+'\\..')
    MyItem = DirectoryItem(UpperDirectory)
    if not node.isChecked():
      MyItem.setText('[Loading, please wait...]')
    else:
      MyItem.setText('.. [%s]' % (os.path.basename(os.path.normpath(node.fullPath()+'\\..')) or os.path.normpath(node.fullPath()+'\\..')))
    self.addItem(MyItem)
    items = list(node.children)
    items.extend(list(node.fileChildren))
    for child in items:
      if child.__class__.__name__ == "FileNode":
        MyItem = FileItem(child)
        self.addItem(MyItem)    
      elif child.__class__.__name__ == "DirectoryNode":
        MyItem = DirectoryItem(child)
        self.addItem(MyItem)    
  
  def __init__(self,parent = None):
    QListWidget.__init__(self,parent)
    self._directory = None
    self._node = None
    self.connect(self,SIGNAL("doubleClicked(QModelIndex)"),self.doubleClicked)

  def doubleClicked(self,model):
    item = self.itemFromIndex(model)
    if type(item) == FileItem:
      self.emit(SIGNAL("openFile(QString)"),item.path())
    elif type(item) == DirectoryItem:
      self.emit(SIGNAL("changeDirectory(QString)"),item.path())



#This is the browser widget containing the directory browser.
class BrowserWidget(QWidget):

  def directory(self):
      return self.DirectoryBrowser.directory()

  def makeWorkingPath(self):
    try:
      os.chdir(self.DirectoryBrowser.directory())
      MyPrefs = Preferences()
      MyPrefs.set('defaultDir',self.DirectoryBrowser.directory())
      MyPrefs.save()
    except WindowsError:
      pass
    
  def directoryBrowser(self):
    return self.DirectoryBrowser
    
  def changeDirectory(self,dir):
    print "Changing directory to ",dir
    self.DirectoryBrowser.changeDirectory(dir)
    
  def __init__(self,parent = None):
    QWidget.__init__(self,parent)

    MyPrefs = Preferences()
    self.Splitter = QSplitter(Qt.Vertical)

    self.FileBrowser = FileBrowser()
    self.DirectoryBrowser = DirectoryTreeView(self.FileBrowser)    
    
    self.Splitter.addWidget(self.DirectoryBrowser)
    self.Splitter.addWidget(self.FileBrowser)
    
    self.Layout = QGridLayout()
    
    self.Layout.addWidget(self.Splitter,0,0)
    
    self.setLayout(self.Layout)

    self.connect(self.FileBrowser,SIGNAL("changeDirectory(QString)"),self.changeDirectory)
    
