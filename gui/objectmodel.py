from pyview.lib.patterns import Subject
import re

class Object(object,Subject):
  
  def __init__(self,name = "[root]",parent = None):
    Subject.__init__(self)
    self._parent = None
    self._children = []
    self._name = name
    self.setParent(parent)
    
  def dump(self):
    return {'name':self.name()}
    
  def Id(self):
    if self.parent() != None:
      return self.parent().Id()+"_"+str(self.parent().indexOfChild(self))
    return "root"
    
  def __len__(self):
    return len(self._children)
    
  def __repr__(self):
    return self.__class__.__name__+"("+self.name()+")"
    
  def isAncestorOf(self,node):
    if node == self:
      return True
    currentNode = node
    while currentNode.parent() != None:
      currentNode = currentNode.parent()
      if currentNode == self:
        return True
    return False
  
  def indexOfChild(self,child):
    if not child in self.children():
      raise KeyError("Not a child of mine!")
    return self._children.index(child)
    
  def addChild(self,child):
    if child.parent() != self:
      child.setParent(self)
    if child not in self._children:
      self._children.append(child)
    
  def removeChild(self,child):
    if child in self._children:
      child.setParent(None)
      del self._children[self._children.index(child)]
      print "Removing child %s from %s" % (child.name(),self.name())
    else:
      raise KeyError("not my child!")
      
  def clearChildren(self):
    for child in self._children:
      child.setParent(None)
    self._children = []
    
  def children(self):
    return self._children
    
  def name(self):
    return self._name
    
  def setName(self,name):
    self._name = name
    
  def setParent(self,parent):
    if self._parent != None:
      oldParent = self._parent
      self._parent = None
      oldParent.removeChild(self)
    self._parent = parent
    if self.parent() != None:
      self.parent().addChild(self)
    
  def parent(self):
    return self._parent
    
class Folder(Object):

  def __init__(self,name,parent = None):
    Object.__init__(self,parent)
    self.setName(name)
    
class File(Object):

  def url(self):
    return self._url

  def dump(self):
    return {'url':self.url()}
    
  def setUrl(self,url):
    self._url = url
    print url
    match = re.search(r"^(.*\\|\/)([^\\\/]*)$",url)
    if match == None:
      print "Couldnt match url..."
      return
    head = match.group(1)
    tail = match.group(2)
    print head,tail
    self.setName(tail)
    
    
  def __init__(self,url,parent = None):
    Object.__init__(self,parent)
    self.setUrl(url)

class Converter(object):

  _objectMap = {Object.__name__: Object, File.__name__ : File, Folder.__name__ : Folder}

  def __init__(self,objectMap = None):
    if objectMap == None:
      self._objectMap = Converter._objectMap
    else:
      self._objectMap = objectMap
    
  def addClass(self,cls):
    self._objectMap[cls.__name__] = {"class":cls}
    
  def removeClass(self,cls):
    if cls.__name__ in self._objectMap:
      del self._ojectMap[cls.__name__]
      
  def dump(self,object):
    params = {}
    key = object.__class__.__name__
    childdumps = []
    for child in object.children():
      childdumps.append(self.dump(child))
    return [key,object.dump(),childdumps]
    
  def load(self,params):
    (key,objparams,children) = params
    if not key in self._objectMap:
      raise KeyError("Don't know how to load objects of type %s" % key)
    object = self._objectMap[key](**objparams)
    for childparams in children:
      object.addChild(self.load(childparams))
    return object
