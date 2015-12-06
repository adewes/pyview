import xml.parsers.expat
import xml.dom.minidom
import xml.dom
import re

class Object(object):

  def __init__(self,name = "[root]",parent = None):
    self._parent = None
    self._children = []
    self._name = name
    self.setParent(parent)
  
  def hasChildren(self):
    if len(self._children) > 0:
      return True
    return False      
  
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
    
  def insertChild(self,index,child):
    if not child in self._children:
      self._children.insert(index,child)
      child.setParent(self)

  def addChild(self,child):
    child.setParent(self)
    if child not in self._children:
      self._children.append(child)
    
  def removeChild(self,child):
    if child in self._children:
      del self._children[self._children.index(child)]
      child.setParent(None)
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
    self._parent = parent
    
  def parent(self):
    return self._parent
   
  @staticmethod 
  def fromXml(doc,node):
  	name = node.getElementsByTagName("name")[0].firstChild.data.lstrip().rstrip()
  	
  	object = Object(name)
  	return object
  	
  def toXml(self,doc,node):
  	name = doc.createElement("name")
  	node.appendChild(name)
  	nameContent = doc.createTextNode(self.name())
  	name.appendChild(nameContent)
  
  def xmlName(self):
  	return "object"
 
class TextNode(Object):

	def __init__(self,name,text = None,parent = None):
		Object.__init__(self,name,parent)
		self.setText(text)
		
	def setText(self,text):
		self._text = text
	
	def text(self):
		return self._text
		
	def toXml(self,doc,node):
		Object.toXml(self,doc,node)
	  	text = doc.createElement("text")
	  	node.appendChild(text)
	  	textContent = doc.createTextNode(self.text())
	  	text.appendChild(textContent)
	
	@staticmethod 
	def fromXml(doc,node):
		object = Object.fromXml(doc,node)
		text = node.getElementsByTagName("text")[0].firstChild.data.lstrip().rstrip()
		
		textNode = TextNode(object.name(),text)
		return textNode
	
	def xmlName(self):
		return "textnode"
			

class XmlConverter(object):

	_objectMap = {"object": Object,"textnode":TextNode}
	
	def __init__(self,objectMap = None):
		if objectMap == None:
			self._objectMap = XmlConverter._objectMap
		else:
			self._objectMap = objectMap
	 
	def addClass(self,name,cls):
		self._objectMap[name] = {"class":cls}
	 
	def removeClass(self,cls):
		if cls.__name__ in self._objectMap:
			del self._ojectMap[cls.__name__]
			
	def dumpToXml(self,object):
		xmldoc = xml.dom.getDOMImplementation()
		doc = xmldoc.createDocument('',"object","")
		node = doc.createElement("objects")
		self.dumpToDocument(object,doc,node)
		return node.firstChild.toprettyxml()
		
	def loadFromXml(self,xmlString):
		doc = xml.dom.minidom.parseString(xmlString)
		return self.loadFromDocument(doc,doc.documentElement)
	 
	def dumpToDocument(self,object,document,element):
		params = {}
		key = object.xmlName()
		objectNode = document.createElement(key)	
		element.appendChild(objectNode)
		object.toXml(document,objectNode)
		childrenNode = document.createElement("children")
		objectNode.appendChild(childrenNode)
		for child in object.children():
			self.dumpToDocument(child,document,childrenNode)
		return True
	 
	def loadFromDocument(self,document,node):
		objectNode = node
		key = objectNode.nodeName
		if not key in self._objectMap:
			raise KeyError("Don't know how to load objects of type {0!s}".format(key))
		object = self._objectMap[key].fromXml(document,objectNode)
		childrenNode = objectNode.getElementsByTagName("children")[0]
		for childNode in childrenNode.childNodes:
			if childNode.nodeType == childNode.TEXT_NODE:
				continue
			object.addChild(self.loadFromDocument(document,childNode))
		return object
##
root = Object("root")
child = TextNode("child","of mine")
root.addChild(child)
child = TextNode("child","another child of mine")
root.addChild(child)

converter = XmlConverter()

print converter.dumpToXml(root)
##

restoredRoot = converter.loadFromXml(converter.dumpToXml(root))

print restoredRoot.name(),":",restoredRoot.children()[1].text()
print root.name(),":",root.children()[1].text()
