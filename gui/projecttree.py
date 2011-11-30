from PyQt4.QtGui import *
from PyQt4.QtCore import *
  
class ProjectModel(QAbstractItemModel):
  
  def __init__(self,root,parent = None):
    QAbstractItemModel.__init__(self,parent)
    self._root = root
    self._nodeList = []
    self._dropAction = Qt.MoveAction
    self._mimeData = None
    
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
    return mimeData

  def addNode(self,node):
    self.beginInsertRows(QModelIndex(),0,0)
    self._root.insertChild(0,node)
    self.endInsertRows()
    
  def dropMimeData(self,data,action,row,column,parent):

    if row == -1:
      row = 0
      
    if data != None:
      parentNode = self.getNode(parent)
      if parentNode == None:
        return False
      print "dropping..."
      if self._dropAction == Qt.MoveAction:
        print "moving..."
        for index in self._mimeData:
          oldParent = index.parent()
          oldParentNode = self.getNode(oldParent)
          node = self.getNode(index)
          rowOfChild = oldParentNode.children().index(node)
          if oldParentNode == parentNode and rowOfChild == row:
            return False
          self.beginMoveRows(oldParent,rowOfChild,rowOfChild,parent,row)
          oldParentNode.removeChild(node)
          parentNode.insertChild(row,node)
          self.endMoveRows()
      else:
        for index in self._mimeData:
          self.beginInsertRows(parent,row,row)
          node = self.getNode(index)
          newNode = copy.deepcopy(node)
          parentNode.insertChild(row,newNode)
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

  def renameNode(self):

    selectedItems = self.selectedIndexes()
    if len(selectedItems) == 1:
      index = selectedItems[0]
      node = self.model().getNode(index)
      if node == None:
        return
      dialog = QInputDialog()
      dialog.setWindowTitle("Change Node Name")
      dialog.setLabelText("New name")
      dialog.setTextValue(node.name())
      dialog.exec_()
      if dialog.result() == QDialog.Accepted:
        node.setName(str(dialog.textValue()))
      
  def deleteNode(self):
    message = QMessageBox(QMessageBox.Question,"Confirm deletion","Are you sure that you want to delete this node?", QMessageBox.Yes | QMessageBox.No)
    message.exec_()
    if message.standardButton(message.clickedButton()) != QMessageBox.Yes:
      return 
    selectedItems = self.selectedIndexes()
    if len(selectedItems) == 1:
      self.model().deleteNode(selectedItems[0])

  def getContextMenu(self,p):
    menu = QMenu()
    selectedItems = self.selectedIndexes()
    if len(selectedItems) == 1:
      renameAction = menu.addAction("Rename")
      self.connect(renameAction,SIGNAL("triggered()"),self.renameNode)
      deleteAction = menu.addAction("Delete")
      self.connect(deleteAction,SIGNAL("triggered()"),self.deleteNode)
    menu.exec_(self.viewport().mapToGlobal(p))
        
  def selectionChanged(self,selected,deselected):
    if len(selected.indexes()) == 1:
      node = self.model().getNode(selected.indexes()[0])
    else:
      pass
    QTreeView.selectionChanged(self,selected,deselected)
