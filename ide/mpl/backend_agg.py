from PySide.QtGui import * 
from PySide.QtCore import *

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
updated = False
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
    self._lock = RLock()
    FigureCanvasQTAgg.__init__(self,*args,**kwargs)
            
  def print_figure(self, filename, dpi=None, facecolor='w', edgecolor='w',
                     orientation='portrait', format=None, **kwargs):
    if self._lock.acquire(blocking = False) == False:
      return
    try:
      FigureCanvasQTAgg.print_figure(self, filename, dpi, facecolor, edgecolor,
                        orientation, format, **kwargs)
    finally:
      self._lock.release()

  def paintEvent(self,e):
    if self._lock.acquire(blocking = False) == False:
      addToUpdateList(self.figure)
      return
    try:
      FigureCanvasQTAgg.paintEvent(self,e)  
    finally:
      self._lock.release()
        
    
##This function should only be called from the main thread!!!
def updateFigures():
  """
  Updates all figures that need to be redrawn.
  """
  global drawWidget
  global drawLabel
  global figureTabs
  global updated
  global drawingWidgets
  if drawingWidgets > 0:
    return
  if matplotlib.is_interactive():
      #We check the update list for figures...
      while len(updateList)>0:
        figure = updateList.pop(0)
        #We redraw each figure that is requested...
        if drawWidget == None:
          drawWidget = QMainWindow()
          drawWidget.setWindowTitle("Figures")
          drawWidget.setMinimumWidth(640)
          drawWidget.setMinimumHeight(480)
          figureTabs = QTabWidget()
          figureTabs.setTabsClosable(True)
          figureTabs.connect(figureTabs,SIGNAL("tabCloseRequested(int)"),closeFigureTab)
          drawWidget.setCentralWidget(figureTabs)
        
        for i in range(0,len(managers)):
          if managers[i].canvas.figure == figure:
            try:
              managers[i].window.update()
              if hasattr(figure,'_name'):
                figureTabs.setTabText(i,figure._name)
              figureTabs.setCurrentIndex(i)
              isUpdating = False
              drawWidget.show()
            except:
              print "A plotting error occured."
              print traceback.print_exc()
            return
            
        MyManager = FigureManagerQTAgg(MyFigureCanvas(figure),1)
              
        managers.append(MyManager)
        try:
          MyManager.window.update()
          if hasattr(figure,'_name'):
            figureTabs.addTab(MyManager.window,figure._name)
          else:
            figureTabs.addTab(MyManager.window,"[new figure]")
          drawWidget.show()
        except:
          print traceback.print_exc()
  
  #We toggle the value of updated...
  updated = not updated
      
def addToUpdateList(fig):
  found = False
  for figure in updateList:
    if figure == fig:
      found = True
  if found == False:
    updateList.append(fig)
  
def figure(name,*args,**kwargs):
  """
  Replacement for matplotlib.figure which supports indexing of figures by strings.
  """
  global figureMap
  global nFigures
  if not name in figureMap:
    figureMap[name] = nFigures
    nFigures+=1
  fig = matplotlib.pyplot.figure(figureMap[name],*args,**kwargs)
  fig._name = name
  return fig
    
##This function can be called from any thread...
def draw_if_interactive():
  """
  Replacement for matplotlib.draw_if_interactive.
  Adds the figure that needs to be redrawn to an update list.
  """
  fig = matplotlib.pyplot.gcf()
  addToUpdateList(fig)
  try:
    fig.canvas.draw()
  except:
    pass