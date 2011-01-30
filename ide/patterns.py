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
    self.updateQueue.append([subject,property,value])
    
  #This function periodically processes the update queue.
  def processUpdateQueue(self):
    while len(self.updateQueue) > 0:
      event = self.updateQueue.pop(0)
      self.updatedGui(*event) 

  def clearUpdateQueue(self):
    self.updateQueue = []
    
  def __init__(self,checkInterval = 1000):
    self.updateQueue =  []
    self.updateQueueTimer = QTimer(self)
    self.updateQueueTimer.setInterval(checkInterval)
    self.connect(self.updateQueueTimer,SIGNAL("timeout()"),self.processUpdateQueue)
    self.updateQueueTimer.start()

