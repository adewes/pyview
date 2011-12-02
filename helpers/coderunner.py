import sys
import time
import traceback
from pyview.lib.patterns import KillableThread,Reloadable,StopThread,Subject
from threading import RLock
import __builtin__,os.path

_importFunction = __builtin__.__import__
_moduleDates = dict()

def _autoReloadImport(name,*a):
  global _importFunction
  global _moduleDates
  if name in sys.modules:
    m = sys.modules[name]
    if hasattr(m,'__file__'):
      filename = m.__file__
      if filename[-4:] == ".pyc":
        filename = filename[:-1]
      if filename[-3:] == ".py":
        mtime = os.path.getmtime(filename)
        if filename in _moduleDates:
          if mtime > _moduleDates[filename]:
            reload(m)
        _moduleDates[filename] = mtime
  return _importFunction(name,*a)

def enableModuleAutoReload():
  __builtin__.__import__ = _autoReloadImport
  
def disableModuleAutoReload():
  __builtin__.__import__ = _importFunction  
  
class CodeThread (KillableThread):

  def __init__(self,code,gv = dict(),lv = dict(),callback = None,source = "<my string>"):
    KillableThread.__init__(self)
    self._gv = gv
    self._lv = lv
    self._source = source
    self._failed = False
    self._callback = callback
    self.code = code
    self._stop = False
    
  def isRunning(self):
    return self.isAlive()
    
  def failed(self):
    return self._failed
    
  def exceptionInfo(self):
    if self.failed() == False:
      return None
    return (self._exception_type,self._exception_value)

  def tracebackInfo(self):
    if self.failed() == False:
        return None
    return self._traceback
    
  def stop(self):
    self._stop = True
    
  def run(self):
    try:
      code = compile(self.code,self._source,'exec')
      exec(code,self._gv,self._lv)
    except StopThread:
      pass
    except:
      self._failed = True
      exc_type, exc_value, exc_traceback = sys.exc_info()
      self._exception_type = exc_type
      self._exception_value = exc_value
      self._traceback = exc_traceback
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
    self._threadID = 0
    self.clear(gv = gv,lv = lv)
    
  def clear(self,gv = dict(),lv = dict()):
    self._gv = gv
    self._lv = dict()
    self._threads = {}
    self._exceptions = {}
    self._tracebacks = {}
    
  def clearExceptions(self):
    self._exceptions = {}
    
  def getException(self,identifier):
    if identifier in self._exceptions:
      return self._exceptions[identifier]
    return None

  def getTraceback(self,identifier):
    if identifier in self._tracebacks:
      return traceback.extract_tb(self._tracebacks[identifier])
    return None

  def formatException(self,identifier):
    exc = self.exception(identifier)
    tb = self.traceback(identifier)
    return traceback.format_exception(exc[0],exc[1],tb)
    

  def gv(self):
    return self._gv
    
  def threadCallback(self,thread):
    lock = RLock()
    lock.acquire()
    if thread.failed():
      self._exceptions[thread._id] = thread.exceptionInfo()
      self._tracebacks[thread._id] = thread.tracebackInfo()
    lock.release()
    
  def lv(self):
    return self._lv
      
  def hasFailed(self,identifier):
    if identifier in self._threads:
      return self._threads[identifier].failed()
      
  def isExecutingCode(self,identifier = None):
    if identifier == None:
      for thread in self._threads.values():
        if thread.isRunning():
          return True
      return False
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
      return -1
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
    ct._id = self._threadID
    self._threadID+=1
    self._threads[identifier] = ct
    ct.setDaemon(True)
    ct.start()
    return ct._id
    
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
      
    def read(self,blocking = True):
      return self._queue.get(blocking)
      
  def __init__(self):
    Process.__init__(self)
    self.daemon = True
    self._commandQueue = Queue()
    self._responseQueue = Queue()
    self._stdoutQueue = Queue()
    self._stderrQueue = Queue()
    self._stdinQueue = Queue()
    self._codeRunner = CodeRunner()
    
  def commandQueue(self):
    return self._commandQueue
    
  def responseQueue(self):
    return self._responseQueue
    
  def stdinQueue(self):
    return self._stdinQueue
    
  def stdoutQueue(self):
    return self._stdoutQueue
    
  def stderrQueue(self):
    return self._stderrQueue
    
  def run(self):
    print "New code process up and running..."
    sys.stderr = self.StreamProxy(self._stderrQueue)
    sys.stdout = self.StreamProxy(self._stdoutQueue)
    sys.stdin = self.StreamProxy(self._stdinQueue)
    while True:
      time.sleep(0.1)
      try:
        while not self.commandQueue().empty():
          (command,args,kwargs) = self.commandQueue().get(False)
          if command == "stop":
            exit(0)
          if hasattr(self._codeRunner,command):
            try:
              f = getattr(self._codeRunner,command)
              r = f(*args,**kwargs)
              self.responseQueue().put(r,False)
            except Exception as e:
              self.responseQueue().put(e,False)
      except KeyboardInterrupt:
        print "Interrupt, exiting..."
      
class MultiProcessCodeRunner():
  
  def __init__(self,gv = dict(),lv = dict()):
    self._codeProcess = CodeProcess()
    self._codeProcess.start()
    self._timeout = 2

  def __del__(self):
    self.terminate()
    
  def setTimeout(self,timeout):
    self._timeout = timeout
    
  def timeout(self):
    return self._timeout
    
  def dispatch(self,command,*args,**kwargs):
    message = (command,args,kwargs)
    if not self._codeProcess.is_alive():
      self.restart()
    self._codeProcess.commandQueue().put(message,False)
    try:
      response = self._codeProcess.responseQueue().get(timeout = self.timeout())
    except:
      response = None
    return response

  def stdin(self,input):
    self._codeProcess.stdinQueue().put(input,False)

  def hasStdout(self):
    return not self._codeProcess.stdoutQueue().empty()

  def stdout(self):
    string = ""
    while not self._codeProcess.stdoutQueue().empty():
      string+=self._codeProcess.stdoutQueue().get(False)
    return string

  def hasStderr(self):
    return not self._codeProcess.stderrQueue().empty()

  def stderr(self):
    string = ""
    while not self._codeProcess.stderrQueue().empty():
      string+=self._codeProcess.stderrQueue().get(False)
    return string
    
  def codeProcess(self):
    return self._codeProcess
    
  def stop(self):
    self._codeProcess.commandQueue().put(("stop",[],{}),False)
    
  def start(self):
    if self._codeProcess.is_alive():
      self.restart()
    else:
      self._codeProcess.start()
    
  def restart(self):
    print "Restarting code runner..."
    self._codeProcess.terminate()
    self._codeProcess = CodeProcess()
    self._codeProcess.start()
    
  def terminate(self):
    if self._codeProcess.is_alive():
      self._codeProcess.terminate()
    
  def __getattr__(self,attr):
    return lambda *args,**kwargs: self.dispatch(attr,*args,**kwargs)
