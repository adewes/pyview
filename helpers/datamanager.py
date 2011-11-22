import sys
import getopt

import os.path

import traceback

from threading import Thread

import PyQt4.uic as uic

from pyview.lib.classes import *
from pyview.lib.datacube import *

#This is a class that manages datacubes
class DataManager(Singleton,Reloadable,ThreadedDispatcher,Subject,Observer):
  
  def __init__(self):
    if hasattr(self,"_initialized"):
      return
      
    self._initialized = True
    print "Initializing data manager..."
    Singleton.__init__(self)
    Reloadable.__init__(self)
    Observer.__init__(self)
    ThreadedDispatcher.__init__(self)
    Subject.__init__(self)
    self._datacubes = []
    self._root = Datacube()
    self._master = None
    
  def updated(self,subject = None,property = None,value = None):
    self.notify("updated",subject)
  
  def master(self):
    return self._master  
  
  def setMaster(self,datacube):
    if self._master != None:
      self._master.notify("isMaster",False)
    self._master = datacube
    if self._master == None:
      return
    self._master.notify("isMaster",True)
    return self._master
    
  def addDatacube(self,datacube,atRoot = False):
    if atRoot == False and not self._master == None:
      if not datacube in self._master.children():
        self._master.addChild(datacube)
        self.notify("added",datacube)
        datacube.attach(self)
      return True
    if not datacube in self._root.children():
      self._root.addChild(datacube)
      self.notify("added",datacube)
      datacube.attach(self)
      return True
        
  def removeDatacube(self,datacube):
    if datacube.parent() != None:
      datacube.parent().removeChild(datacube)
    else:
      self._root.removeChild(datacube)
    
  def datacubes(self):
    return self._datacubes
    
  def clear(self):
    self._root.removeChildren(self._root.children())
    self._root = Datacube()
    self.notify("cleared")

  def root(self):
    return self._root    
    
  def saveAll(self,filename):
    self._root.savetxt(filename)