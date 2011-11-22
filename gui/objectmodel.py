from pyview.lib.patterns import Subject

class Object(object,Subject):
  
  def __init__(self,parent = None):
    Subject.__init__(self)
    self.setParent(parent)
    self._children = []
    
  def addChild(self,child):
    if not child in self._children:
      self._children.append(child)
    child.setParent(self)
    
  def removeChild(self,child):
    if child in self._children:
      child.setParent(None)
      del self._children[self._chilrden.index(child)]
      
  def clearChildren(self):
    for child in self._children:
      child.setParent(None)
    self._children = []
    
  def setParent(self,parent):
    self._parent = parent
    
  def parent(self):
    return self._parent
    
class Folder(Object):

  def name(self):
    return self._name
    
  def setName(self,name):
    self._name = name
    
  def __init__(self,name,parent = None):
    Object.__init__(self,parent)
    self.setName(name)
    
class File(Object):

  def name(self):
    return self._name
    
  def setName(self,name):
    self._name = name
    
  def url(self):
    return self._url
    
  def setUrl(self,url):
    self._url = url
    
  def __init__(self,name,url,parent = None):
    Object.__init__(self,parent)
    self.setName(name)


