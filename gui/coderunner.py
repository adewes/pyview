import time
import sys
from threading import Thread

from PyQt4.QtGui import *
from PyQt4.QtCore import *

"""
This model helps to execute GUI code in a QT main thread.
"""

def _runGuiCodeSignal(f):
	f()

def execInGui(f):
  _ensureGuiThreadIsRunning()
  global app
  if app == None:
    raise Exception("Invalid application handle!")
  app.emit(SIGNAL("runGuiCode(PyQt_PyObject)"),f)
	 
def _createApplication():
  global app
  app = QApplication(sys.argv)
  app.setQuitOnLastWindowClosed(False)
  app.connect(app,SIGNAL("runGuiCode(PyQt_PyObject)"),_runGuiCodeSignal)
  if app.thread() != QThread.currentThread():
  	raise Exception("Cannot start QT application from side thread! You will have to restart your process...")
  app.exec_()
	
def _ensureGuiThreadIsRunning():
  global app
  global setUp
  app = QApplication.instance()
  if app == None:
    thread = Thread(target = _createApplication)
    thread.start()
    while thread.is_alive() and (app == None or app.startingUp()):
      time.sleep(0.01)