import sys
import getopt
import re
import struct
import time
import pickle
from math import *

from pyview.lib.datacube import Datacube
from pyview.lib.patterns import Subject,Observer,KillableThread

class Ramp(Subject):

  def __init__(self,name = "noname"):
    Subject.__init__(self)
    self._children = []
    self._name = name
    self._parent = None

  def parent(self):
    return self._parent
    
  def setParent(self,parent):
    self._parent = parent

  def tostring(self):
    return pickle.dumps(self)

  def fromstring(cls,string):
    return pickle.loads(string)

  fromstring = classmethod(fromstring)

  def len(self):
    return len(self._children)

  def clear(self):
    self._children = []
    self.notify("clear")

  def name(self):
    return self._name
  
  def setName(self,name):
    self._name = name

  def children(self):
    return self._children
    
  def hasChildren(self):
    if len(self._children) > 0:
      return True
    return False
    
  def insertChild(self,index,child):
    if not child in self._children:
      self._children.insert(index,child)
      child.setParent(self)
      self.notify("insertChild",[index,child])
    
  def addChild(self,child):
    if not child in self._children:
      self._children.append(child)
      child.setParent(self)
      self.notify("addChild",child)
    
  def removeChild(self,child):
    for i in range(0,len(self._children)):
      if child == self._children[i]:
        del self._children[i]
        child.setParent(None)
        self.notify("removeChild",child)
        return
    
class RampReference:

  def __init__(self,ramp = None):
    self._fakeRamp = Ramp()
    self._parent = None
    self._initialization = ""
    self._ramp = None
    if isinstance(ramp,RampReference):
      self._ramp = ramp.ramp()
    else:
      self._ramp = ramp

  def parent(self):
    return self._parent
    
  def setParent(self,parent):
    self._parent = parent

  def initialization(self):
    return self._initialization
    
  def setInitialization(self,initialization):
    self._initialization = str(initialization)
    
  def hasChildren(self):
    return False

  def ramp(self):
    if self._ramp == self:
      raise Exception("woa!")
    return self._ramp
    
  def name(self):
    if not hasattr(self,"_ramp"):
      return "none..."
    if self._ramp == "None":
      return "broken ramp reference"
    return "->"+self._ramp.name()
    
  def __getattr__(self,attr):

    if attr[0] == '_':
      raise AttributeError()
      
    print "Getting attribute %s" % attr
    if self._ramp != None and hasattr(self._ramp,attr):
      print "Getting attribute from ramp..."
      return getattr(self._ramp,attr)
    raise AttributeError()
        
  def run(self,datacube, gv = globals(),lv = globals()):
    print "Running a ramp reference..."
    lv['data'] = datacube
    exec(self._initialization,gv,lv)
    return self.ramp().run(datacube,gv,lv)

    
#This ramp changes some parameter and calls a given function at each point in the parameter space.
class ParameterRamp(Ramp):
  
  def __init__(self,name = "undefined"):
    Ramp.__init__(self,name)
    self._range = [0]
    self._generator = ""
    self._code = ""
    self._rangeGenerator = ""
    self._finish = ""
    self._stopped = True
    self._paused = False
    self._finish = ""
    self._progress = 0
    self._forward = True
    self._currentValue = None
    
  def code(self):
    return self._code
    
  def goForward(self):
    self._forward = True
    
  def goBackward(self):
    self._forward = False
  
  def isPaused(self):
    return self._paused
    
  def isRunning(self):
    if not self._stopped and not self._paused:
      return True
    return False

  def fullStop(self):
    self.stop()
    for child in self._children:
      child.fullStop()
        
  def isStopped(self):
    return self._stopped
        
  def pause(self):
    self._paused = True
    self.notify("paused")
    
  def fullPause(self):
    self.pause()
    for child in self._children:
      child.fullPause()
    
  def resume(self):
    self._paused = False
    self.notify("resumed")

  def fullResume(self):
    self.resume()
    for child in self._children:
      child.resume()
    
  def stop(self):
    self._stopped = True
    
  def currentValue(self):
    return self._currentValue
    
  def runGenerator(self,gv = globals(),lv = globals(),data = None):
    lv['data'] = data
    exec(self._generator,gv,lv)
    
  def runRangeGenerator(self,gv = globals(),lv = globals(),data = None,updateRange = False):
    lv['data'] = data
    exec(self._rangeGenerator,gv,lv)
    if 'ramp' in lv:
      if updateRange and hasattr(self,'_range') and hasattr(self,'_index') and list(self._range) != list(lv["ramp"]):
        print "Updating ramp position..."
        currentValue = self._range[self._index]
        minDistance = 0
        minIndex = 0
        for i in range(0,len(lv["ramp"])):
          distance = fabs(lv["ramp"][i]-currentValue)
          if i == 0 or distance < minDistance:
            minDistance = distance
            minIndex = i
          if distance == 0:
            break
        print "Setting current index to %i" % minIndex
        self._index = minIndex
      self._range = lv['ramp']
    else:
      self._range = [0]
    return self._range

    
  def runFinish(self,gv = globals(),lv = globals(),data = None):
    if 'ramp' in lv.keys():
      del lv['ramp']
    lv['data'] = data
    exec(self._finish,gv,lv)
    
  def progress(self):
    return self._progress
      
  def setCode(self,code):
    self._code = str(code)

  def finish(self):
    return self._finish
    
  def generator(self):
    return self._generator
  
  def setFinish(self,finish):
    self._finish = str(finish)
  
  def setGenerator(self,generator):
    self._generator = str(generator)
  
  def setRangeGenerator(self,rangeGenerator):
    self._rangeGenerator = str(rangeGenerator)
    
  def rangeGenerator(self):
    return self._rangeGenerator
    
  def run(self,datacube, gv = globals(),lv = globals()):
    try:
      if self._stopped == False:
        self.fullStop()
        raise Exception("Infinite recursion error!")
      self.notify("started")
      self._stopped = False
      self._paused = False
      self._progress = 0
      self.goForward()
      self._index = 0
      self.runRangeGenerator(gv = gv, lv = lv,data = datacube)
      self.runGenerator(gv = gv, lv = lv,data = datacube)
      while self._index < len(self._range):
        x = self._range[self._index]
        self._progress = float(self._index)/float(len(self._range))*100
        if self._stopped:
          self.runFinish(gv = gv, lv = lv,data = datacube)
          return datacube
        wasPaused = False
        if self.isPaused():
          wasPaused = True
        while self.isPaused():
          if self.isStopped():
            self.runFinish(gv = gv, lv = lv,data = datacube)
            return datacube
          time.sleep(1)
        if wasPaused:
          self.runRangeGenerator(gv = gv,lv = lv,data = datacube,updateRange = True)
        self._currentValue = x
        self.notify("currentValue",x)
        lv['x'] = x
        lv['data'] = datacube
        exec(self._code,gv,lv)
        for child in self._children:
          childcube = Datacube()
          datacube.addChild(childcube)
          child.run(childcube,gv,lv)
        self._index+=1
      self.runFinish(gv = gv, lv = lv,data = datacube)
      return datacube
    finally:
      self._stopped = True
      self._paused = False
      self.notify("stopped")

