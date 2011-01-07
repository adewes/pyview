from pyview.lib.patterns import Singleton
from pyview.conf.parameters import params

import os
import os.path
import shelve

class Preferences(Singleton):

  _initialized = False

  def __init__(self,*args,**kwargs):
    if self._initialized == True:
      return
    self._initialized = True
    Singleton.__init__(self)
    self.init(*args,**kwargs)
    
  def init(self,path = None,filename = 'preferences.dat'):
    if path == None:
      path = os.path.normpath(os.path.dirname(__file__)+"\\..\\config")
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
    print "Saving preferences..."
    self.save()
    
  def save(self):
    self._prefs.sync()

