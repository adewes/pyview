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
      exec(code,self._gv,self._gv)
    except StopThread:
      print "Thread termination requested, exiting..."
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

  def __init__(self,gv = dict(),lv = dict()):
    Reloadable.__init__(self)
    Subject.__init__(self)
    self._gv = gv
    self._lv = lv
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
    
  def executeCode(self,code,identifier,filename = None):
    if self.isExecutingCode(identifier):
      return False
    ct = CodeThread(code,source = filename,lv = self._lv,gv = self._gv,callback = self.threadCallback)
    self._threads[identifier] = ct
    ct.setDaemon(True)
    ct.start()
    return True