import sys
import getopt
import re
import struct
import time
import pickle
from math import *

from pyview.lib.datacube import Datacube
from pyview.lib.patterns import Subject,Observer,KillableThread

class Ramp(Subject):

  def __init__(self,name = "noname"):
    Subject.__init__(self)
    self._children = []
    self._name = name
    self._code = ""
    self._parent = None

  def parent(self):
    return self._parent
    
  def code(self):
    return self._code
    
  def setCode(self,code):
    self._code = code
    
  def setParent(self,parent):
    self._parent = parent

  def tostring(self):
    return pickle.dumps(self)

  def fromstring(cls,string):
    return pickle.loads(string)

  fromstring = classmethod(fromstring)

  def len(self):
    return len(self._children)

  def clear(self):
    self._children = []
    self.notify("clear")

  def name(self):
    return self._name
  
  def setName(self,name):
    self._name = name

  def children(self):
    return self._children
    
  def hasChildren(self):
    if len(self._children) > 0:
      return True
    return False
    
  def insertChild(self,index,child):
    if not child in self._children:
      self._children.insert(index,child)
      child.setParent(self)
      self.notify("insertChild",[index,child])
    
  def addChild(self,child):
    if not child in self._children:
      self._children.append(child)
      child.setParent(self)
      self.notify("addChild",child)
    
  def removeChild(self,child):
    for i in range(0,len(self._children)):
      if child == self._children[i]:
        del self._children[i]
        child.setParent(None)
        self.notify("removeChild",child)
        return

