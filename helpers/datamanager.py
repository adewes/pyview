import sys
import getopt

import os.path

import traceback

from threading import Thread

import PyQt4.uic as uic

from pyview.lib.patterns import Singleton,Reloadable,ThreadedDispatcher,Subject,Observer

#This is a class that manages datacubes
class DataManager(Singleton,Reloadable,ThreadedDispatcher,Subject,Observer):
  
  """
  The DataManager is a Singleton class which can be used to keep track of datacubes. Just call addDatacube() to add a datacube to the DataManager. pyview.gui.datamanager.DataManager provides a graphical frontend of the DataManager class.
  """
  
  def __init__(self):
    if hasattr(self,"_initialized"):
      return
    self._initialized = True
    Singleton.__init__(self)
    Reloadable.__init__(self)
    Observer.__init__(self)
    ThreadedDispatcher.__init__(self)
    Subject.__init__(self)
    self._datacubes = []
  
  def autoPlot(self,datacube,clear = False):
    """
    Triggers an autoPlot of the selected datacube, i.e. a graphical frontend that observeres the state of the data manager will be notified that 'datacube' should be replotted.
    """
    self.notify("autoPlot",[datacube,clear])
  
  def updated(self,subject = None,property = None,value = None):
    self.notify("updated",subject)
      
  def addDatacube(self,datacube):
    """
    Adds a datacube to the data manager.
    """
    if not datacube in self._datacubes:
      self._datacubes.append(datacube)
      self.notify("addDatacube",datacube)
      datacube.attach(self)
      return True
        
  def removeDatacube(self,datacube):
    """
    Removes a datacube from the data manager.
    """
    if datacube in self._datacubes:
      del self._datacubes[self._datacubes.index(datacube)]
      self.notify("removeDatacube",datacube)
    
  def datacubes(self):
    """
    Returns the datacubes.
    """
    return self._datacubes
    
  def clear(self):
    """
    Removes all datacubes from the data manager.
    """
    self._datacubes = []
    self.notify("cleared")
