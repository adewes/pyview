"""
Some convenience classes for managing instruments and frontpanels.
"""

import traceback
import socket

try:
  import visa
  from visa import VI_ERROR_CONN_LOST,VI_ERROR_INV_OBJECT
  from visa import VisaIOError
  from visa import Error
  from pyvisa import vpp43
except:
  print "Cannot import Visa!"

DEBUG = False

from pyview.lib.patterns import *

class Instrument(ThreadedDispatcher,Reloadable,object):
  
  def __init__(self,name = ""):
    Subject.__init__(self)
    ThreadedDispatcher.__init__(self)
    self._name = name
    self._states = []
    self._stateCount = 0
    self.daemon = True
    
  def initialize(self,*args,**kwargs):
    pass
    
  def __str__(self):
    return "Instrument \"%s\"" % self.name()
    
  def saveState(self,name):
    """
    Saves the state of the instrument.
    """
    return None
    
  def pushState(self):
    self._states.append(self.saveState("state_"+str(self._stateCount)))
    self._stateCount+=1
    
  def popState(self):
    if len(self._states) > 0:
      state = self._states.pop()
      self.restoreState(state)
    
  def restoreState(self,state):
    """
    Restores the state of the instrument given by "state".
    
    "state" can be of any type. For instruments that can store configuration data on a hard disk, "state" could be the name of the file on the disk.
    For other instruments, "state" could contain all relevant instrument parameters in a dictionary.
    """
    pass
    
  def name(self):
    return self._name
  
  def parameters(self):
    """
    Redefine this function to return all relevant instrument parameters in a dictionary.
    """
    return dict()
          
class VisaInstrument(Instrument):

    """
    A class representing an instrument that can be interfaced via NI VISA protocol.
    """

    def __init__(self,name = "",visaAddress = None):
      """
      Initialization
      """
      Instrument.__init__(self,name)
      self._handle = None
      self._visaAddress = visaAddress

    def getHandle(self,forceReload = False):
      """
      Return the VISA handle for this instrument.
      """
      if forceReload or self._handle == None:
        try:
          if self._handle != None:
            try:
              self._handle.close()
            except:
              pass
            self._handle = None
        except:
          pass
        self._handle = visa.instrument(self._visaAddress)
      return self._handle
      
    def executeVisaCommand(self,method,*args,**kwargs):
      """
      This function executes a VISA command.
      If the VISA connection was lost, it reopens the VISA handle.
      """
      try:
        returnValue = method(*args,**kwargs)
        return returnValue
      except Error as error:
        print "Invalidating Visa handle..."
        self._handle = None
        raise

    def __getattr__(self,name):
      """
      Forward all unknown method calls to the VISA handle.
      """
      handle = self.getHandle()
      if hasattr(handle,name):
        attr = getattr(handle,name)
        if hasattr(attr,"__call__"):
          return lambda *args,**kwargs: self.executeVisaCommand(attr,*args,**kwargs)
        else:
          return attr
      raise AttributeError("No such attribute: %s" % name)

import pickle
import cPickle
from struct import pack,unpack

class Command:

  def __init__(self,name = None,args =None,kwargs =None):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    self._name = name
    self._args = args
    self._kwargs = kwargs
    
  def name(self):
    return self._name
    
  def args(self):
    return self._args
    
  def kwargs(self):
    return self._kwargs

  def toString(self):
    pickled = cPickle.dumps(self,cPickle.HIGHEST_PROTOCOL)
    s = pack("l",len(pickled))
    return s+pickled

  @classmethod
  def fromString(self,string):
    m = cPickle.loads(string)
    return m
    
class ServerConnection:

  def __init__(self,ip,port):
    self._ip = ip
    self._port = port
    self._socket = self.openConnection()
    
  def openConnection(self):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt( socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((self._ip, self._port))
    return sock
    
  def ip(self):
    return self._ip
    
  def port(self):
    return self._port

  def _send(self,command,args =None,kwargs =None):
    #We set some socket options that help to avoid errors like 10048 (socket already in use...)
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    command = Command(name = command,args = args,kwargs = kwargs)
    sock = self._socket
    try:
      sock.send(command.toString())
      lendata = sock.recv(4)
      if len(lendata) == 0:
        raise Exception("Connection to server %s port %d failed." % (self._ip,self._port))
      length = unpack("l",lendata)[0]
      received = sock.recv(length)
      binary = received
      while len(received)>0 and len(binary) < length:
        received = sock.recv(length-len(binary))
        binary+=received
      if len(binary) == 0:
        return None
      response = Command().fromString(binary)
      if response == None:
        raise Exception("Connection to server %s port %d failed." % (self._ip,self._port))
      if response.name() == "exception" and len(response.args()) > 0:
        raise response.args()[0]
      return response.args()[0]
    except:
      self._socket = self.openConnection()
      raise
    
  def __getattr__(self,attr):
    return lambda *args,**kwargs:self._send(attr,args,kwargs)

class RemoteInstrument(ThreadedDispatcher,Reloadable,object):

  def __init__(self,name,server,baseclass = None, args =None,kwargs =None,forceReload = False):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    ThreadedDispatcher.__init__(self)
    Reloadable.__init__(self)
    server.initInstrument(name,baseclass,args,kwargs,forceReload)
    self._server = server
    self._name = name
    self._baseclass = baseclass
    self._args = args
    self._kwargs = kwargs
    
  def remoteDispatch(self,command,args =None,kwargs =None):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    result =  self._server.dispatch(self._name,command,args,kwargs)
    self.notify(command,result)
    return result
    
  def __str__(self):
    return "Remote Instrument \"%s\" on server %s:%d" % (self.name(),self._server.ip(),self._server.port())
    
  def name(self):
    """We redefine name, since it is already defined as an attribute in Thread
    """ 
    return self.remoteDispatch("name")

  def __getitem__(self,key):
    return self.remoteDispatch("__getitem__",[str(key)])

  def __setitem__(self,key,value):
    print "Setting %s" % key
    return self.remoteDispatch("__setitem__",[key,value])

  def __delitem__(self,key):
    return self.remoteDispatch("__delitem__",[key])
    
  def getAttribute(self,attr):
    return self.remoteDispatch("__getattr__",[attr])
    
  def setAttribute(self,attr,value):
    return self.remoteDispatch("__setattr__",[attr,value])
      
  def __getattr__(self,attr):
    return lambda *args,**kwargs:self.remoteDispatch(attr,args,kwargs)
        