DEBUG = False

import threading
import time
import ctypes
import timeit
import sys
import copy
import weakref

class Singleton(object):

  _instance = None
  
  def delete(self):
    _instance = None
          
  def __new__(cls, *args, **kwargs):
      if not cls._instance:
          cls._instance = super(Singleton, cls).__new__(
                             cls)
                             
      return cls._instance

def _async_raise(tid, excobj):
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(excobj))
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        # """if it returns a number greater than one, you're in trouble, 
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")
 
class StopThread(Exception):
  pass
 
class KillableThread(threading.Thread):
    
    def raise_exc(self, excobj):
        assert self.isAlive(), "thread must be started"
        for tid, tobj in threading._active.items():
            if tobj is self:
                _async_raise(tid, excobj)
                return
        
        # the thread was alive when we entered the loop, but was not found 
        # in the dict, hence it must have been already terminated. should we raise
        # an exception here? silently ignore?
    
    def terminate(self):
        self.raise_exc(SystemExit)

class Subject:

    def __getstate__(self):
      variables = copy.copy(self.__dict__)
      if "_observers" in variables:
        del variables["_observers"]
      return variables
      
    def __setstate__(self,state):
      self.__dict__ = state
      self._observers = []

    def __init__(self):
        self._observers = []
        self.isNotifying = False

    def attach(self, observer):
        r = weakref.ref(observer)
        if not r in self._observers:
            self._observers.append(r)

    def setObservers(self,observers):
      if not observers == None:
        self._observers = observers
      else:
        self._observers = []
    
    def observers(self):
      return self._observers

    def detach(self, observer):
        r = weakref.ref(observer)
        try:
            if DEBUG:
              print "Removing observer."
            self._observers.remove(r)
        except ValueError:
          pass

    def notify(self,property = None, value = None,modifier = None):
      try:
        #This is to avoid infinite notification loop, e.g. when the notified class calls a function of the subject that triggers another notify and so on...
        if self.isNotifying:
          #print "WARNING: notify for property %s of %s was called recursively by modifier %s, aborting." % (property,str(self),str(modifier))
          return False
        self.isNotifying = True
        deadObservers = []
        for observer in self._observers:
            if observer() == None:
              deadObservers.append(observer)
              continue
            if modifier != observer():
                try:
                  if hasattr(observer(),'updated'):
                    observer().updated(self,property,value)
                except:
                  print "An error occured when notifying observer {0!s}.".format(str(observer()))
                  print sys.exc_info()
                  raise
        for deadObserver in deadObservers:
          del self._observers[self._observers.index(deadObserver)]
        self.isNotifying = False
      except:
        print sys.exc_info()
        raise
      finally:
        self.isNotifying = False
        

class Dispatcher(Subject):

    def __init__(self):
      Subject.__init__(self)
      self._currentId = 0
      self.queue = []
      self._stopDispatcher = False
      
    def error(self):
      return None
      
    def clearQueue(self):
      self.queue = []
      
    def stop(self):
      self._stopDispatcher = True
      self.clearQueue()
      
    def unstop(self):
      self._stopDispatcher = False
      
    def stopped(self):
      return self._stopDispatcher
            
    def processQueue(self):
      start = time.time()
      if len(self.queue) == 0:
        return
      while len(self.queue) > 0:
        (dispatchId,command,callback,args,kwargs) = self.queue.pop()
        mname = command
        if hasattr(self, mname):
            method = getattr(self, mname)
            result = method(*args,**kwargs)
            self.notify(command,result)
            if not callback == None:
              callback(dispatchId,result)
        else:
            self.error()
      elapsed = (time.time() - start)

    def dispatchCB(self, command, callback, *args, **kwargs):
        self.queue.insert(0,[self._currentId,command,callback,args,kwargs])
        self._currentId+=1
        self._stopDispatcher = False
        
    def queued(self,ID):
      for entry in self.queue:
        if entry[0] == ID:
          return True
      return False

    def dispatch(self, command, *args, **kwargs):
        self.queue.insert(0,[self._currentId,command,None,args,kwargs])
        self._currentId+=1
        self._stopDispatcher = False

class ThreadedDispatcher(Dispatcher,KillableThread):

    def __init__(self):
      Dispatcher.__init__(self)
      KillableThread.__init__(self)

    def restart(self):
      if self.isAlive():
        return
      KillableThread.__init__(self)
      self.start()
    
    def run(self):
      self.processQueue()

    def dispatchCB(self,command,callback,*args,**kwargs):
      Dispatcher.dispatchCB(self,command,callback,*args,**kwargs)
      if not self.isAlive():
        self.restart()

    def dispatch(self,command,*args,**kwargs):
      Dispatcher.dispatch(self,command,*args,**kwargs)
      if not self.isAlive():
        self.restart()

class Observer:

  def __init__(self):
    pass
  
  def updated(self,subject = None,property = None,value = None):
    pass
    
class Reloadable(object):
  
  #This function dynamically reloads the module that defines the class and updates the current instance to the new class.
  def reloadClass(self):
    self.beforeReload()
    print "Reloading {0!s}".format(self.__module__)
    newModule = reload(sys.modules[self.__module__])
    self.__class__ = eval("newModule.{0!s}".format(self.__class__.__name__))
    self.onReload()
    
  def beforeReload(self,*args,**kwargs):
    pass
    
  def onReload(self,*args,**kwargs):
    pass
    
  def __init__(self):
    pass
