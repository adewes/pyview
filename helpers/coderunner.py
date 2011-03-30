import sys

from pyview.lib.patterns import KillableThread,Reloadable,StopThread,Subject
from threading import RLock

class CodeThread (KillableThread):

  def __init__(self,code,gv = dict(),lv = dict(),callback = None,source = "<my string>"):
    KillableThread.__init__(self)
    self._gv = gv
    self._lv = lv
    self._source = source
    self._failed = False
    self._callback = callback
    self.code = code
    
  def isRunning(self):
    return self.isAlive()
    
  def failed(self):
    return self._failed
    
  def exceptionInfo(self):
    if self.failed() == False:
      return None
    return (self._exception_type,self._exception_value,self._traceback)
    
  def run(self):
    try:
      code = compile(self.code,self._source,'exec')
      exec(code,self._gv,self._lv)
    except StopThread:
      pass
    except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      self._exception_type = exc_type
      self._exception_value = exc_value
      self._traceback = exc_traceback
      self._failed = True
      raise
    finally:
      if not self._callback == None:
        self._callback(self)
  

class CodeRunner(Reloadable,Subject):

  _id = 0
  
  def getId(self):
    CodeRunner._id+=1
    return CodeRunner._id

  def __init__(self,gv = dict(),lv = dict()):
    Reloadable.__init__(self)
    Subject.__init__(self)
    self.clear(gv = gv,lv = lv)
    
  def clear(self,gv = dict(),lv = dict()):
    self._gv = gv
    self._lv = dict()
    self._threads = dict()
    self._exceptions = []
    
  def clearExceptions(self):
    self._exceptions = []
    
  def exceptions(self):
    return self._exceptions

  def gv(self):
    return self._gv
    
  def threadCallback(self,thread):
    lock = RLock()
    lock.acquire()
    if thread.failed():
      self._exceptions.append(thread.exceptionInfo())
      self.notify("exceptions",self.exceptions())
    lock.release()
    
  def lv(self):
    return self._lv
      
  def hasFailed(self,identifier):
    if identifier in self._threads:
      return self._threads[identifier].failed()
      
  def isExecutingCode(self,identifier):
    if not identifier in self._threads:
      return False
    if self._threads[identifier] == None:
      return False
    return self._threads[identifier].isRunning()
    
  def stopExecution(self,identifier):
    if not self.isExecutingCode(identifier):
      return
    if not identifier in self._threads:
      return
    self._threads[identifier].terminate()
    
  def executeCode(self,code,identifier,filename = None, lv = None,gv = None):
    if self.isExecutingCode(identifier):
      return False
    if lv == None:
      if not identifier in self._lv:
        self._lv[identifier] = dict()
      lv = self._lv[identifier]
    if gv == None:
      gv = self._gv
    
    class GlobalVariables:
      
      def __init__(self,gv):
        self.__dict__ = gv
        
    gvClass = GlobalVariables(gv)
    
    lv["gv"] = gvClass
    
    ct = CodeThread(code,source = filename,lv = lv,gv = lv,callback = self.threadCallback)
    self._threads[identifier] = ct
    ct.setDaemon(True)
    ct.start()
    return True
    
from multiprocessing import *
from pyview.helpers.coderunner import *
import time
import numpy
import threading

class CodeProcess(Process):

  class StreamProxy(object):
  
    def __init__(self,queue):
      self._queue = queue
      
    def write(self,output):
      self._queue.put(output)
      
  def __init__(self):
    Process.__init__(self)
    self._commandQueue = Queue()
    self._responseQueue = Queue()
    self._stdoutQueue = Queue()
    self._stderrQueue = Queue()
    self._codeRunner = CodeRunner()
    
  def commandQueue(self):
    return self._commandQueue
    
  def responseQueue(self):
    return self._responseQueue
    
  def stdoutQueue(self):
    return self._stdoutQueue
    
  def stderrQueue(self):
    return self._stderrQueue
    
  def run(self):
    sys.stderr = self.StreamProxy(self._stderrQueue)
    sys.stdout = self.StreamProxy(self._stdoutQueue)
    while True:
      while not self.commandQueue().empty():
        (command,args,kwargs) = self.commandQueue().get()
        if command == "stop":
          exit(0)
        if hasattr(self._codeRunner,command):
          f = getattr(self._codeRunner,command)
          r = f(*args,**kwargs)
          self.responseQueue().put(r)

    
class MultiProcessCodeRunner():
  
  def __init__(self,gv = dict(),lv = dict()):
    self._codeProcess = CodeProcess()
    self._codeProcess.start()
    
  def dispatch(self,command,*args,**kwargs):
    message = (command,args,kwargs)
    self._codeProcess.commandQueue().put(message)
    try:
      response = self._codeProcess.responseQueue().get(timeout = 2)
    except:
      response = None
    return response
    
  def codeProcess(self):
    return self._codeProcess
    
  def stop(self):
    
    self._codeProcess.commandQueue().put(("stop",[],{}))
    
  def restart(self):
    print "Restarting code runner..."
    self._codeProcess.terminate()
    self._codeProcess = CodeProcess()
    self._codeProcess.start()
    
  def terminate(self):
    self._codeProcess.terminate()
    
  def __getattr__(self,attr):
    return lambda *args,**kwargs: self.dispatch(attr,*args,**kwargs)
