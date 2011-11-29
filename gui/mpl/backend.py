from PyQt4.QtGui import * 
from PyQt4.QtCore import *
from PyQt4.QtSvg import *

import matplotlib
from matplotlib.backends.backend_agg import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import FigureManagerQTAgg

from pyview.gui.coderunner import execInGui

figures = {}

def draw():
  figure = matplotlib.pyplot.gcf()
  execInGui(lambda figure = figure: drawInGui(figure))

  
def draw_if_interactive():
  if not matplotlib.is_interactive():
    return
  draw()
  
show = draw

def drawInGui(figure):
  figureNumber = figure.number
  if not figureNumber in figures:
    widget = FigureManagerQTAgg(FigureCanvasQTAgg(figure),figureNumber)
    widget.window.setAttribute(Qt.WA_DeleteOnClose,on = False)
    figures[figureNumber] = widget
  else:
    widget = figures[figureNumber]
  widget.show()
  widget.canvas.draw()
      