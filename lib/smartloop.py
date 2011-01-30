import os
import time
import sys

from pyview.lib.patterns import Subject,Singleton,Reloadable

class SmartLoop(Subject,Reloadable):

  def __init__(self,values = range(0,100),name = 'loop'):
    Subject.__init__(self)
    Reloadable.__init__(self)
    self._factory = LoopFactory()
    self._index = 0
    self._values = values
    self._factory.addLoop(self)
    self._forward = True
    self._paused = False
    self._stopped = False
    self._name = name
    
  def setName(self,name):
    self._name = name
    
  def name(self):
    return self._name
    
  def currentValue(self):
    if self._index < len(self._values):
      return self._values[self._index]
    return None
    
  def index(self):
    return self._index
    
  def values(self):
    return self._values
    
  def rewind(self):
    self._index = 0
    self.notify("rewind")
    
  def pause(self):
    self._paused = True
    self.notify("pause")
    
  def resume(self):
    self._paused = False
    self.notify("resume")
    
  def stop(self):
    self._stopped = True
    self.notify("stop")
    
  def stopped(self):
    return self._stopped
    
  def paused(self):
    return self._paused
    
  def goBackward(self):
    self._forward = False
    self.notify("goBackward")
    
  def goForward(self):
    self._forward = True
    self.notify("goForward")

  def next(self):
    while self._paused:
      time.sleep(1)
      if self._stopped:
        raise StopIteration()
    if self._index >= len(self._values) or self._stopped:
      self.notify("finished")
      raise StopIteration()
    v = self._values[self._index]
    self.notify("next",v)
    if self._forward:
      self._index+=1
    else:
      self._index-=1
    if self._index < 0:
      raise StopIteration()
    return v
    
  def __iter__(self):
    return self
  
class LoopFactory(Singleton,Subject,Reloadable):
  
  def __init__(self):
    """
    Initialize the loop factory.
    """
    if hasattr(self,'_initialized'):
      return
    self._initialized = True
    Subject.__init__(self)
    Singleton.__init__(self)
    Reloadable.__init__(self)
    self._loops = []
    
  def removeLoop(self,smartLoop):
    if smartLoop in self._loops:
      self._loops.remove(smartLoop)
      smartLoop.detach(self)
      self.notify("removeLoop",smartLoop)
    
  def addLoop(self,smartLoop):
    print "Adding loop..."
    if not smartLoop in self._loops:
      self.notify()
      self._loops.append(smartLoop)
      smartLoop.attach(self)
      self.notify("addLoop",smartLoop)
      
  def loops(self):
    return self._loops
  
  def clear(self):
    for r in self._loops:
      self.removeLoop(r)
      
  def updated(self,subject,property,value = None):
    if subject in self._loops:
      if property == 'finished':
        self.removeLoop(subject)
    else:
      subject.detach(self)
  
