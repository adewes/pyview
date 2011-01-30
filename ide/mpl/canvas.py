from PyQt4.QtGui import * 
from PyQt4.QtCore import *
from PyQt4.uic import *
import sys
import os
import os.path
import tempfile

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import FigureManagerQTAgg
from matplotlib.figure import Figure
from pyview.ide.editor.codeeditor import CodeEditor

from matplotlib import rcParams
from math import fabs

rcParams['font.family'] = 'sans-serif'
rcParams['font.size'] = '12'
rcParams['interactive'] = True
rcParams['font.sans-serif'] = ['Tahoma']

class FigureManager(FigureManagerQTAgg):
  pass

class CanvasDialog(QDialog):
  
  def __init__(self,canvas,parent = None):
    QDialog.__init__(self,parent)
    self.setFixedWidth(640)
    layout = QGridLayout()
    self.setLayout(layout)
    self._canvas = canvas
    self.setWindowTitle(self._canvas.title()+" properties")
    self.tabs = QTabWidget()
    layout.addWidget(self.tabs,0,0)
    self.codeEditor = CodeEditor()
    self.codeEditor.activateHighlighter()
    if self._canvas.extraCode() != None:
      self.codeEditor.setPlainText(self._canvas.extraCode())
    self.cancelButton = QPushButton("Cancel")
    self.updateButton = QPushButton("Update")
    self.OKButton = QPushButton("OK")
    buttonsLayout = QBoxLayout(QBoxLayout.RightToLeft)
    buttonsLayout.addWidget(self.cancelButton)
    buttonsLayout.addWidget(self.updateButton)
    buttonsLayout.addWidget(self.OKButton,)
    buttonsLayout.addStretch(0)
    layout.addLayout(buttonsLayout,1,0)
    self.tabs.addTab(self.codeEditor,"Custom code")
    self.connect(self.updateButton,SIGNAL("clicked()"),self.updateFigure)
    self.connect(self.OKButton,SIGNAL("clicked()"),self.updateAndClose)
    self.connect(self.cancelButton,SIGNAL("clicked()"),self.close)
    
  def updateAndClose(self):
    self.updateFigure()
    self.close()
    
  def updateFigure(self):
    self._canvas.draw()
    self._canvas.setExtraCode(str(self.codeEditor.toPlainText()))
    self._canvas.execExtraCode()

class MyMplCanvas(FigureCanvas):

    def onPress(self,event):
      if event.button == 1:
        self._pressed = True
        self._pressEvent = event
    
    def extraCode(self):
      return self._extraCode
      
    def setExtraCode(self,code):
      self._extraCode = code
    
    def execExtraCode(self):
      if self._extraCode == None:
        return
      lv = self.__dict__
      exec(self._extraCode,lv,lv)
      
    def mouseMoveEvent(self,e):
      try:
        FigureCanvas.mouseMoveEvent(self,e)
      except:
        pass
             
    def onMove(self,event):
      self._moveLabel.show()
      if event.xdata == None:
        self._moveLabel.hide()
        return
      self._moveLabel.setText(QString(r"x = %g, y = %g" % (event.xdata,event.ydata)))
      self._moveLabel.adjustSize()
      offset = 10
      if self.width()-event.x < self._moveLabel.width():
        offset = -10 - self._moveLabel.width()
      self._moveLabel.move(event.x+offset,self.height()-event.y)
                
    def zoomTo(self,rect):
        self.axes.set_xlim(rect.left(),rect.right())
        self.axes.set_ylim(rect.bottom(),rect.top())
        self.axes.set_autoscale_on(False) 
        self.draw()

    def title(self):
      return "Figure"
        
    def contextMenuEvent(self, event):    
      menu = QMenu(self)
      autoscaleAction = menu.addAction("Autoscale / Zoom Out")
      saveAsAction = menu.addAction("Save figure as...")
      fastDisplayAction = menu.addAction("Open as PDF")
      propertiesAction = menu.addAction("Properties")
      fontSizeMenu = menu.addMenu("Font size")
      fontSizes = dict()
      for i in range(6,16,2):
        fontSizes[i] = fontSizeMenu.addAction("%d px" % i)
      action = menu.exec_(self.mapToGlobal(event.pos()))
      if action == saveAsAction:
        filename = QFileDialog.getSaveFileName()
        if not filename == '':
          self._fig.set_size_inches( self._width, self._height )
          self._fig.savefig(str(filename))
      elif action == fastDisplayAction:

        dialog = QInputDialog()
        dialog.setWindowTitle("Save and open as *.pdf")
        dialog.setLabelText("Filename")
        dialog.setTextValue("")
        
        dialog.exec_()
        
        if dialog.result() == QDialog.Accepted:
          filename = dialog.textValue()
        if filename == "":
          filename = "no name"
        baseName = ""+filename
        filename += ".pdf"
        cnt = 1
        while os.path.exists(filename):
          filename = baseName+ "_%d.pdf" % cnt
          cnt+=1
        try:
          services = QDesktopServices()
          if not filename == '':
            self._fig.set_size_inches( self._width, self._height )
            self._fig.savefig(str(filename))
            url = QUrl("file:///%s" % filename)
            services.openUrl(url)
        finally:
          pass
      elif action == propertiesAction:
        try:
          reload(sys.modules["pyview.lib.canvas"])
          from pyview.lib.canvas import CanvasDialog
        except ImportError:
          pass
        if not self._dialog == None:
          self._dialog.hide()
        self._dialog = CanvasDialog(self)
        self._dialog.setModal(False)
        self._dialog.show()
      elif action == autoscaleAction:
        self.autoScale()
      for fontSize in fontSizes.keys():
        if action == fontSizes[fontSize]:
          print "Setting font size to %d" % fontSize
          rcParams['font.size'] = str(fontSize)
          self.draw()
                         
    def autoScale(self):
      self.axes.set_autoscale_on(True)
      self.axes.relim() 
      self.axes.autoscale_view()
      self.draw()
    
                          
    def onRelease(self,event):
      if event.button == 1:
        self._pressed = False
        if self._pressEvent.xdata == None or event.xdata == None:
          return
        oldRect = QRectF()
        oldRect.setLeft(self.axes.get_xlim()[0])
        oldRect.setRight(self.axes.get_xlim()[1])
        oldRect.setBottom(self.axes.get_ylim()[0])
        oldRect.setTop(self.axes.get_ylim()[1])
        rect = QRectF()
        rect.setLeft(min(self._pressEvent.xdata,event.xdata))
        rect.setRight(max(self._pressEvent.xdata,event.xdata))
        rect.setBottom(min(self._pressEvent.ydata,event.ydata))
        rect.setTop(max(self._pressEvent.ydata,event.ydata))
        if fabs(rect.width()) >= 0.01*fabs(oldRect.width()) and fabs(rect.height()) >=fabs(0.01*oldRect.height()):
          self.zoomTo(rect)
    
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=5, dpi=60):


        fig = Figure(figsize=(width, height), dpi=dpi)
        self._fig = fig
        self._dialog = None
        self._width = width
        self._height = height
        self._dpi = dpi

        FigureCanvas.__init__(self, fig)
        
        self.setFixedWidth(self._dpi*self._width)
        self.setFixedHeight(self._dpi*self._height)
        
        self._isDrawing = False
        self._extraCode = """#axes.set_title("test")
#axes.set_xlabel("frequency [GHz]")"""
        self.axes = fig.add_subplot(111)
        self.axes.set_autoscale_on(True) 
        self.axes.hold(True)


        self.setParent(parent)

        self._moveLabel = QLabel("",self)
        self._moveLabel.setText("tes")
        self._moveLabel.hide()
        self._moveLabel.setStyleSheet("font-size:14px; margin:5px; padding:4px; background:#FFFFFF; border:2px solid #000;")
        
        self.mpl_connect('button_press_event', self.onPress)
        self.mpl_connect('button_release_event', self.onRelease)
        self.mpl_connect('motion_notify_event', self.onMove)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

class MatplotlibCanvas(MyMplCanvas):
  pass