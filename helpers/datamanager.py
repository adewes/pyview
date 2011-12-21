import sys
import getopt

import os.path

import traceback

from threading import Thread

import PyQt4.uic as uic

from pyview.lib.classes import *

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
  
  def autoPlot(self,datacube,clear = False):
    self.notify("autoPlot",[datacube,clear])
  
  def updated(self,subject = None,property = None,value = None):
    self.notify("updated",subject)
      
  def addDatacube(self,datacube):
    if not datacube in self._datacubes:
      self._datacubes.append(datacube)
      self.notify("addDatacube",datacube)
      datacube.attach(self)
      return True
        
  def removeDatacube(self,datacube):
    if datacube in self._datacubes:
      del self._datacubes[self._datacubes.index(datacube)]
      self.notify("removeDatacube",datacube)
    
  def datacubes(self):
    return self._datacubes
    
  def clear(self):
    self._datacubes = []
    self.notify("cleared")