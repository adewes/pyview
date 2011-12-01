from PyQt4.QtGui import *
from PyQt4.QtCore import *
import pyview.gui.objectmodel as objectmodel
  
class ProjectModel(QAbstractItemModel):
  
  def __init__(self,root,parent = None):
    QAbstractItemModel.__init__(self,parent)
    self._root = root
    self._nodeList = []
    self._dropAction = Qt.MoveAction
    self._mimeData = None
    
  def setProject(self,project):
    self.beginResetModel()
    self._root = project
    self.endResetModel()
    
    
  def project(self):
    return self._root
    
  def headerData(self,section,orientation,role):
    if section == 1:
      return QVariant(QString(u""))
            
  def deleteNode(self,index):
    parent = self.parent(index)
    node = self.getNode(index)
    parentNode = self.getNode(parent)
    if parentNode == None:
      parentNode = self._root
    self.beginRemoveRows(parent,index.row(),index.row())
    parentNode.removeChild(node)
    self.endRemoveRows()
    
  def getIndex(self,node):
    if node in self._nodeList:
      return self._nodeList.index(node)
    self._nodeList.append(node)
    index = self._nodeList.index(node)
    return index
    
  def getNode(self,index):
    if not index.isValid():
      return self._root
    return self._nodeList[index.internalId()]
    
  def parent(self,index):
    if index == QModelIndex():
      return QModelIndex()
    node = self.getNode(index)
    if node == None:
      return QModelIndex()  
    if node.parent() == None:
      return QModelIndex()
    if node.parent().parent() == None:
      return QModelIndex()
    else:
      grandparent = node.parent().parent()
      row = grandparent.children().index(node.parent())
      return self.createIndex(row,0,self.getIndex(node.parent()))

  def hasChildren(self,index):
    node = self.getNode(index)
    if node == None:
      return True
    if node.hasChildren():
      return True
    return False
    
  def data(self,index,role = Qt.DisplayRole):
    node = self.getNode(index)
    if role == Qt.DisplayRole:
      return QVariant(node.name())
    return QVariant()
    
  def index(self,row,column,parent):
    parentNode = self.getNode(parent)
    if parentNode == None:
      if row < len(self._root.children()):
        return self.createIndex(row,column,self.getIndex(self._root.children()[row]))
    elif row < len(parentNode.children()):
      return self.createIndex(row,column,self.getIndex(parentNode.children()[row]))
    return QModelIndex()
    
  def columnCount(self,parent):
    return 1

  def supportedDropActions(self):
    return Qt.MoveAction | Qt.CopyAction
    
  def setDropAction(self,action):
    self._dropAction = action
    
  def rowCount(self,parent):
    if not parent.isValid():
      return len(self._root.children())
    node = self.getNode(parent)
    return len(node.children())    

  def flags(self,index):
    defaultFlags = QAbstractItemModel.flags(self,index)
    if index.isValid():
      return Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | defaultFlags
    else:
      return Qt.ItemIsDropEnabled | defaultFlags

  def mimeData(self,indexes):
    mimeData = QMimeData()
    mimeData.setData("projecttree/internalMove","")
    self._moveIndexes = indexes
    return mimeData

  def addNode(self,node,parent = QModelIndex()):
    self.beginInsertRows(parent,0,0)
    parentNode = self.getNode(parent)
    parentNode.insertChild(0,node)
    self.endInsertRows()
    
  def dropMimeData(self,data,action,row,column,parent):

    if row == -1:
      row = 0
            
    if data != None:
      parentNode = self.getNode(parent)
      if parentNode == None:
        return False
      if data.hasFormat("projecttree/internalMove"):
        if self._dropAction == Qt.MoveAction:
          parentNode = self.getNode(parent)
          while type(parentNode) is not objectmodel.Folder:
            if parentNode.parent() == None:
              return False
            parentNode = parentNode.parent()
            parent = self.parent(parent)
          for index in self._moveIndexes:
            oldParent = index.parent()
            oldParentNode = self.getNode(oldParent)
            node = self.getNode(index)
            rowOfChild = oldParentNode.children().index(node)
            if oldParentNode == parentNode and rowOfChild == row:
              return False
            if node.isAncestorOf(parentNode):
              return False
            self.beginMoveRows(oldParent,rowOfChild,rowOfChild,parent,0)
            oldParentNode.removeChild(node)
            parentNode.insertChild(0,node)
            self.endMoveRows()
      elif data.hasUrls():
        index = parent
        while type(parentNode) != objectmodel.Folder:
          if parentNode.parent() == None:
            return False
          index = self.parent(index)
          parentNode = parentNode.parent()
        for url in data.urls():
          if url.toLocalFile() != "":
            fileNode = objectmodel.File(url = str(url.toLocalFile()))
            self.beginInsertRows(index,len(parentNode),len(parentNode))
            parentNode.addChild(fileNode)
            self.endInsertRows()
    return True

class ProjectView(QTreeView):

  def __init__(self,parent = None):
    QTreeView.__init__(self,parent)
    self.setAcceptDrops(True)
    self.setDragEnabled(True)
    self.setContextMenuPolicy(Qt.CustomContextMenu)
    self.connect(self, SIGNAL("customContextMenuRequested(const QPoint &)"), self.getContextMenu)

  def dragMoveEvent(self,e):
    e.accept()
    
  def dragEnterEvent(self,e):
    e.acceptProposedAction()
            
  def createNewFolder(self):
    selectedIndices = self.selectedIndexes()
    if len(selectedIndices) == 0:
      index = QModelIndex()
    else:
      index = selectedIndices[0]
    
    node = self.model().getNode(index)
    
    while type(node) != objectmodel.Folder:
      if node.parent() == None:
        return
      node = node.parent()
      index = self.model().parent(index)
      
    dialog = QInputDialog()
    dialog.setWindowTitle("New Folder")
    dialog.setLabelText("Name")
    dialog.setTextValue("")
    dialog.exec_()
    if dialog.result() == QDialog.Accepted:
      node = objectmodel.Folder(str(dialog.textValue()))
      self.model().addNode(node,index)

  def editCurrentItem(self):

    selectedItems = self.selectedIndexes()
    if len(selectedItems) == 1:
      index = selectedItems[0]
      node = self.model().getNode(index)
      if node == None or type(node) != objectmodel.Folder:
        return
      dialog = QInputDialog()
      dialog.setWindowTitle("Edit Folder")
      dialog.setLabelText("Name")
      dialog.setTextValue(node.name())
      dialog.exec_()
      if dialog.result() == QDialog.Accepted:
        node.setName(str(dialog.textValue()))
      
  def deleteCurrentItem(self):
    selectedItems = self.selectedIndexes()
    if len(selectedItems) == 1:
      message = QMessageBox(QMessageBox.Question,"Confirm deletion","Are you sure that you want to delete this node?", QMessageBox.Yes | QMessageBox.No)
      message.exec_()
      if message.standardButton(message.clickedButton()) != QMessageBox.Yes:
        return 
      self.model().deleteNode(selectedItems[0])

  def mouseDoubleClickEvent(self,event):
    index = self.indexAt(event.pos())
    if index.isValid():
      node = self.model().getNode(index)
      if type(node) == objectmodel.File:
        self.emit(SIGNAL("openFile(PyQt_PyObject)"),node.url())
        event.accept()
        return
    QTreeView.mouseDoubleClickEvent(self,event)

  def getContextMenu(self,p):
    menu = QMenu()
    selectedItems = self.selectedIndexes()
    if len(selectedItems) == 1:
      renameAction = menu.addAction("Edit")
      self.connect(renameAction,SIGNAL("triggered()"),self.editCurrentItem)
      deleteAction = menu.addAction("Delete")
      self.connect(deleteAction,SIGNAL("triggered()"),self.deleteCurrentItem)
    menu.exec_(self.viewport().mapToGlobal(p))
        
  def selectionChanged(self,selected,deselected):
    if len(selected.indexes()) == 1:
      node = self.model().getNode(selected.indexes()[0])
    else:
      pass
    QTreeView.selectionChanged(self,selected,deselected)
