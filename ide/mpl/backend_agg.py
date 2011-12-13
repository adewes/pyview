from PyQt4.QtGui import * 
from PyQt4.QtCore import *

from matplotlib.backends.backend_agg import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import FigureManagerQTAgg
import matplotlib
import matplotlib.pyplot
import traceback
import time
from threading import RLock

import StringIO

drawWidget = None
figureTabs = None
managers = []
canvasList = []
updateList = []
drawLabel = None
figureMap = dict()
nFigures = 0
figures = None
doUpdateFigures = False
drawingWidgets = 0

class MyMainWindow(QMainWindow):
  def __init__(self,parent = None):
    QMainWindow.__init__(self,parent)
    
def closeFigureTab(i):
  """
  Remove the figure window from the tab.
  """
  global figureTabs
  window = figureTabs.widget(i)
  if window.close():
    del managers[i]
    window.destroy()
    figureTabs.removeTab(i)
    
class MyFigureCanvas(FigureCanvasQTAgg):
  
  """
  An attempt to make FigureCanvas thread-safe...
  """
  
  def __init__(self,*args,**kwargs):
    FigureCanvasQTAgg.__init__(self,*args,**kwargs)
            
            
  def print_figure(self, filename, dpi=None, facecolor='w', edgecolor='w',
                     orientation='portrait', format=None, **kwargs):
    if self.figure._lock.acquire(blocking = False) == False:
      print "Failed to acquire lock..."
      return
    try:
      FigureCanvasQTAgg.print_figure(self, filename, dpi, facecolor, edgecolor,
                        orientation, format, **kwargs)
    finally:
      self.figure._lock.release()

  def paintEvent(self,e):
#    if self.figure._lock.acquire(blocking = False) == False:
#      addToUpdateList(self.figure)
#      return
    try:
      FigureCanvasQTAgg.paintEvent(self,e)  
    finally:
      pass
#      self.figure._lock.release()
        
    
##This function should only be called from the main thread!!!
def updateFigures():
  """
  Updates all figures that need to be redrawn.
  """
  global drawWidget
  global drawLabel
  global figureTabs
  global drawingWidgets
  global doUpdateFigures

  if drawingWidgets > 0:
    return
  
  if not doUpdateFigures:
    return
    
  doUpdateFigures = False
  
  #We check the update list for figures...
  while len(updateList)>0:
    figure = updateList.pop(0)
    #We redraw each figure that is requested...
    if drawWidget == None:
      drawWidget = QMainWindow()
      drawWidget.setWindowTitle("Figures")
#          drawWidget.setMinimumWidth(640)
#          drawWidget.setMinimumHeight(480)
      figureTabs = QTabWidget()
      figureTabs.setTabsClosable(True)
      figureTabs.connect(figureTabs,SIGNAL("tabCloseRequested(int)"),closeFigureTab)
      drawWidget.setCentralWidget(figureTabs)
    
    for i in range(0,len(managers)):
      if managers[i].canvas.figure == figure:
        try:
          managers[i].canvas.draw_idle()
          if hasattr(figure,'_name'):
            figureTabs.setTabText(i,figure._name)
#          figureTabs.setCurrentIndex(i)
          isUpdating = False
          drawWidget.show()
        except:
          print "A plotting error occured."
          print traceback.print_exc()
        return
        
    MyManager = FigureManagerQTAgg(MyFigureCanvas(figure),1)
          
    managers.append(MyManager)
    try:
      MyManager.canvas.draw_idle()
      if hasattr(figure,'_name'):
        figureTabs.addTab(MyManager.window,figure._name)
      else:
        figureTabs.addTab(MyManager.window,"[new figure]")
      drawWidget.show()
    except:
      print traceback.print_exc()

      
def addToUpdateList(fig):
  if fig in updateList:
    return
  updateList.append(fig)
  
def figure(name,*args,**kwargs):
  """
  Replacement for matplotlib.figure which supports indexing of figures by strings.
  """
  global figureMap
  global nFigures
  name = str(name)
  if not name in figureMap:
    figureMap[name] = nFigures
    nFigures+=1
  fig = matplotlib.pyplot.figure(figureMap[name],*args,**kwargs)
  if not hasattr(fig,'_lock'):
    fig._lock = RLock()
  fig._name = name
  return fig

def show():
    """
    Show all the figures and enter the qt main loop
    This should be the last line of your script
    """
    global doUpdateFigures
    doUpdateFigures = True
        
def draw_if_interactive():
  """
  Replacement for matplotlib.draw_if_interactive.
  Adds the figure that needs to be redrawn to an update list.
  """
  fig = matplotlib.pyplot.gcf()
  addToUpdateList(fig)
  if matplotlib.is_interactive():
    doUpdateFigures = True
    if not hasattr(fig,'_lock'):
      fig._lock = RLock()
    try:
      fig._lock.acquire()
      fig.canvas.draw()
    except:
      pass
    finally:
      fig._lock.release()