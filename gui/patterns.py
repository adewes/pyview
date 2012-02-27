from PyQt4.QtCore import *

from pyview.lib.patterns import Observer

#This is an observer class especially tailored to widgets. Instead of processing "updated" calls directly,
#this class queues them and periodically calls a processing function in the main thread that handles all the events.
class ObserverWidget(Observer):
  
  #This function gets called from the notifying (possibly non-GUI) thread.
  #It is not safe to call GUI-related functions from this function.
  def updatedThread(self,subject = None,property = None,value = None):
    pass
    
  #This function gets called from the main (GUI) thread.
  #It is safe to call GUI-related functions from this function.
  def updatedGui(self,subject = None,property = None,value = None):
    pass
  
  #We intercept the "update" call from the subject and queue it.
  def updated(self,subject = None,property = None,value = None):
    self.updatedThread(subject,property,value)
    if not self._connected:
      self.connect(self,SIGNAL("processUpdate(PyQt_PyObject)"),self.processUpdate,Qt.QueuedConnection | Qt.UniqueConnection)  
      self._connected = True
    self.emit(SIGNAL("processUpdate(PyQt_PyObject)"),[subject,property,value])
    
  def processUpdate(self,args):
    self.updatedGui(*args)
    
  def __init__(self):
    Observer.__init__(self)
    self._connected = False

