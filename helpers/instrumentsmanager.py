import sys
import getopt

import os.path


import traceback
from threading import Thread

import xmlrpclib

import re

from pyview.lib.classes import *

class InstrumentHandle:

  """
  Contains information on a given instrument:
  """

  def instrumentModule(self):
    return self._module
  
  def __init__(self,name,baseClass,instrument,module = None,remote = False,remoteServer = None,args = [],kwargs = {}):
    self._name = name.lower()
    self._baseClass = baseClass
    self._instrument = instrument
    self._module = module
    self._remote = remote
    self._remoteServer = remoteServer
    self._args = args
    self._kwargs = kwargs
  
  def args(self):
    return self._args
    
  def kwargs(self):
    return self._kwargs
    
  def baseClass(self):
    return self._baseClass
    
  def remote(self):
    return self._remote
  
  def name(self):
    return self._name
    
  def instrument(self):
    return self._instrument
    

class RemoteManager:

  """
  The remote version of the instrument manager. Loads and reloads instruments and dispatches commands to them. 
  """
  
  def __init__(self,manager):
    self._manager = manager
    self._observers = dict()
    
  def __getattr__(self,name):
    return getattr(self._manager,name)
        
  def initInstrument(self,name,baseclass = None,args = [],kwargs = {},forceReload = False):
    if self._manager.initInstrument(name,args = args,baseclass = baseclass,kwargs = kwargs,forceReload = forceReload) == None:
      return False
    return True
    
  def reloadInstrument(self,name,baseclass = None,args = [],kwargs = {}):
    print "Reloading %s,%s with arguments:" % (name,baseclass),args,kwargs
    self._manager.reloadInstrument(name,baseclass,args = args,kwargs = kwargs)
    return True

  def dispatch(self,instrument,command,args = [],kwargs = {}):
    instr = self._manager.getInstrument(instrument)
    if hasattr(instr,command):
      method = getattr(instr,command)
      return  method(*args,**kwargs)
    raise Exception("Unknown function name: %s" % command)

class Manager(Subject,Singleton):

  """
  Manages the creation and reloading of instruments.
  """

  _initialized = False
  
  def __init__(self):
    """
    Initialize the instrument manager.
    """
    if self._initialized == True:
      return
    self._initialized = True
    if DEBUG:
      print "Initializing instruments manager."
    Subject.__init__(self)
    Singleton.__init__(self)
 
    self._instruments = dict()

  def saveState(self,stateName,instruments = [],withInitialization = True):
    """
    Return a dictionary containing the parameters of all the instruments.
    """
    state = dict()
    for name in self._instruments.keys():
      try:
        if instruments == [] or name in instruments:
          print "Storing state of instrument \"%s\"" % name
          state[name] = dict()
          state[name]["state"]=self.getInstrument(name).saveState(stateName)
          if withInitialization:
            state[name]["args"] = self.handle(name).args()
            state[name]["kwargs"] = self.handle(name).kwargs()
            state[name]["baseClass"] = self.handle(name).baseClass()
      except:
        print "Could not save the state of instrument %s:" % name
        print traceback.print_exc()
    return state
    
  
  def restoreState(self,state,withInitialization = True):
    """
    Restores the state of all instruments that are references in the "state" parameter AND that are already loaded.
    """
    for name in state.keys():
      if "args" in state[name].keys() and "kwargs" in state[name].keys() and withInitialization:
        self.initInstrument(name,state[name]["baseClass"],state[name]["args"],state[name]["kwargs"])
      if name in self._instruments.keys():
        try:
          print "Restoring state of instrument \"%s\"" % name
          self.getInstrument(name).restoreState(state[name]["state"])
        except:
          print "Could not restore the state of instrument %s:" % name
          print traceback.print_exc()

  def parameters(self):
    """
    Return a dictionary containing the parameters of all the instruments.
    """
    params = dict()
    for name in self._instruments.keys():
      try:
        params[name]=self.getInstrument(name).parameters()
      except:
        pass
    return params

  def handle(self,name):
    """
    Return the handle for a given instrument.
    """
    try:
      return self._instruments[name.lower()]
    except KeyError:
      return None
    
  def frontPanel(self,name):
    """
    Returns the frontpanel for the given instrument.
    """
    handle = self.handle(name)
    if handle == None:
      return None
    moduleName = handle._baseClass
    frontPanelModule =  __import__("frontpanels.%s" % moduleName,globals(),globals(),[moduleName],-1)
    reload(frontPanelModule)
    frontPanelModule =  __import__("frontpanels.%s" % moduleName,globals(),globals(),[moduleName],-1)
    frontPanel = frontPanelModule.Panel(handle._instrument)
    frontPanel.setWindowTitle("%s front panel" % name)
    return frontPanel
    
    
  def initRemoteInstrument(self,address,baseclass = None,args = [],kwargs = {},forceReload = False):
    """
    Loads a remote instrument, either through the HTTP XML-RPC protocol or through the custom Remote Instrument Protocol (RIP)
    """
    result =  re.match(r'^rip\:\/\/(.*)\:(\d+)\/(.*)$',address)
    if result:
      (host,port,name) = result.groups(0)
      try:
        remoteServer = ServerConnection(result.groups(0)[0],int(result.groups(0)[1]))
      except socket.error:
        print "Connection to remote host failed!"
        return None
    else:
      result = re.match(r'^http\:\/\/(.*)\:(\d+)\/(.*)$',address)
      if result:
        (host,port,name) = result.groups(0)
        try:
          remoteServer = xmlrpclib.ServerProxy("http://%s:%s" % (host,port))
        except SocketError:
          return None
      else:
        return None

    if baseclass == None:
      baseclass = name

    if name.lower() in self._instruments and forceReload == False:
      instrument = self._instruments[name.lower()]
      return instrument.instrument()      
    else:
      baseclass = baseclass.lower()
      try:
        instrument = RemoteInstrument(name,remoteServer,baseclass,args,kwargs,forceReload)
      except:
        print "Cannot initialize instrument:"
        traceback.print_exc()
        return None
      handle = InstrumentHandle(name,baseclass,instrument,args = args,kwargs = kwargs,remote = True,remoteServer = remoteServer)
      self._instruments[name.lower()] = handle
      self.notify("instruments",self._instruments)
      return handle.instrument()
    
  def hasInstrument(self,name):
    if name.lower() in self._instruments:
      return True
    return False
    
  def getInstrument(self,name):
    if name.lower() in self._instruments:
      return self._instruments[name.lower()].instrument()
    else:
      return None
    
  def _isUrl(self,name):
    if re.match(r'^rip\:\/\/',name) or  re.match(r'^http\:\/\/',name):
      return True
    return False
    
  def initInstrument(self,name,baseclass = None,args = [],kwargs = {},forceReload = False):
    """
    Loads an instrument. "name" is either the plain name of the instrument to be initialized (e.g. "vna1") or an URL (e.g. "rip://localhost:8000/vna1")
    Returns the reference to the instrument object, or None if the initialization fails.
    """
    print "Initializing instrument %s" % name
    if name.lower() in self._instruments:
      if forceReload:
        return self.reloadInstrument(name,args = args,kwargs = kwargs)
      else:
        return self._instruments[name.lower()].instrument()
    else:

      if self._isUrl(name):
        return self.initRemoteInstrument(name,baseclass,args,kwargs,forceReload)

      if baseclass == None:
        baseclass = name
      baseclass = baseclass.lower()

      try:
        instrumentModule = __import__("instruments.%s" % baseclass,globals(),globals(),[baseclass],-1)
        reload(instrumentModule)
      except ImportError:
        print "instrument: Unknown instrument class: %s" % baseclass
        print traceback.print_exc()
        return None

      try:
        instrument = instrumentModule.Instr(name = name)
        instrument.initialize(*args,**kwargs)
      except:
        print "An error occured when loading instrument \"%s\":" % name
        print traceback.print_exc()
        return None        

      handle = InstrumentHandle(name,baseclass,instrument,instrumentModule,args = args,kwargs = kwargs)
      self._instruments[name.lower()] = handle
      self.notify("instruments",self._instruments)
      return handle.instrument()
  
  def stopInstrument(self,handle):
    try:
      if handle.instrument().isAlive() == False:
        return
      handle.instrument().stop()
      handle.instrument().join(2)
      if handle.instrument().isAlive():
        print "Error when stopping instrument %s " % handle.name()
        handle.instrument().terminate()
      else:
          if DEBUG:
            print "Stopped %s" % handle.name()
    except:
      print "Unknown error when stopping the instrument: %s" % handle.name()
      print traceback.print_exc()
  
  def reloadInstrument(self,name,baseclass = None,args = [],kwargs = {}):
    print "Reloading %s" %  name
    if not name.lower() in self._instruments:
      raise KeyError("No such instrument: %s" % name)

    handle = self._instruments[name.lower()]
    if handle.instrument().isAlive():
      raise Exception("Cannot reload instrument while it is running...")
#    self.stopInstrument(handle)

    if args != []:
      passedArgs = args
      handle._args = args
    else:
      passedArgs = handle.args()
    if kwargs != {}:
      passedKwArgs = kwargs
      handle._kwargs = kwargs
    else:
      passedKwArgs = handle.kwargs()


    if handle._remote == True:
      if handle._remoteServer.hasInstrument(handle._name):
        handle._remoteServer.reloadInstrument(handle._name,handle._baseClass,passedArgs,passedKwArgs)
      else:
        handle._remoteServer.initInstrument(handle._name,handle._baseClass,passedArgs,passedKwArgs)
      self.notify("instruments",self._instruments)
      return handle.instrument()
    else:
      reload(handle._module)
      newClass = handle._module.Instr
      handle.instrument().__class__ = newClass
      handle.instrument().initialize(*passedArgs,**passedKwArgs)
      self.notify("instruments",self._instruments)
      return handle.instrument()

    
  def instruments(self):
    return self._instruments
