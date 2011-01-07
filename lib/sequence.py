from threading import RLock
import time

class Sequence():

  def __init__(self,values = None):
    self._values = values
    self._index = 0
    self._stopped = False
    self._paused = False
    self._lock = RLock()
    
  def init(self,values):
    self._values = values
    self._index = 0
 
  def paused(self):
    return self._paused
    
  def stopped(self):
    return self._stopped
        
  def valid(self):
    if self._index >= len(self._values) or self._stopped or self._paused:
      return False
    return True
        
  def current(self):
    with self._lock:
      if self.stopped():
        return False
      while self.paused():
        time.sleep(1)
      if self._values == None or self._index >= len(self._values):
        return False
      return self._values[self._index]
    
  def next(self):
    with self._lock:
      self._index+=1
      return self.current()
      
  def previous(self):
    with self._lock:
      if self._index >0:
        self._index -= 1
      else:
        return False
      return self.current()
    
  def reset(self):
    with self._lock:
      self._index = 0
    
  def pause(self):
    with self._lock:
      self._paused = True
    
  def run(self):
    with self._lock:
      self._paused = False
      self._stopped = False
  
  def stop(self):
    with self._lock:
      self._stopped = True