import time
import sys
from threading import Thread
import threading

from PyQt4.QtGui import *
from PyQt4.QtCore import *

signalConnected = False

"""
This model helps to execute GUI code in a QT main thread.
"""

def _runGuiCodeSignal(f):
  print "Executing..."
  print "Python Thread ID:"+str(threading.current_thread().ident)
  print "QT Thread ID:"+str(QThread.currentThread())
  f()
	
def execInGui(f):
  _ensureGuiThreadIsRunning()
  global app
  if app == None:
    raise Exception("Invalid application handle!")
  print "Emitting signal..."
  print "Python Thread ID:"+str(threading.current_thread().ident)
  print "QT Thread ID:"+str(QThread.currentThread())
  app.emit(SIGNAL("runGuiCode(PyQt_PyObject)"),f)
  
def _createApplication():
  global app
  global signalConnected
  global _runGuiCodeSignal
  app = QApplication(sys.argv)
  app.setQuitOnLastWindowClosed(False)
  app.connect(app,SIGNAL("runGuiCode(PyQt_PyObject)"),_runGuiCodeSignal,Qt.AutoConnection | Qt.UniqueConnection)
  signalConnected = True
  if app.thread() != QThread.currentThread():
  	raise Exception("Cannot start QT application from side thread! You will have to restart your process...")
  app.exec_()
	
def _ensureGuiThreadIsRunning():
  global app
  global signalConnected
  global _runGuiCodeSignal
  app = QApplication.instance()
  if app == None:
    print "Creating new application..."
    thread = Thread(target = _createApplication)
    thread.start()
    while thread.is_alive() and (app == None or app.startingUp()):
      time.sleep(0.01)
  else: 
    if not signalConnected:
      print "Adding signal handler to application.."
      print app.connect(app,SIGNAL("runGuiCode(PyQt_PyObject)"),_runGuiCodeSignal,Qt.AutoConnection | Qt.UniqueConnection)
      signalConnected = True