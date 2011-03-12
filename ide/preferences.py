from pyview.lib.patterns import Singleton
from pyview.config.parameters import params

import os
import os.path
import shelve

class Preferences():

  def __init__(self,path = None,filename = 'preferences.dat'):
    if path == None:
      raise Exception("You must specify a directory for storing the application preferences!")
    self._appFolder = path
    if os.path.isdir(self._appFolder) == False:
      os.mkdir(self._appFolder)
    print self._appFolder
    self._filename = filename 
    self._prefs = shelve.open(self._appFolder+'/'+self._filename)
    
  def set(self,name,value):
    self._prefs[name] = value
  
  def shelve(self):
    return self._prefs
   
  def get(self,name):
    try:
      return self._prefs[name]
    except KeyError:
      return None

  def loadFromFile(filename = None):
    pass
    
  def __del__(self):
    self.save()
    
  def save(self):
    self._prefs.sync()

