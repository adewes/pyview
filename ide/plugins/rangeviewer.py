import sys
import getopt


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from pyview.ide.preferences import *
import PyQt4.uic as uic
import pickle
import cPickle
import copy


from pyview.ide.patterns import ObserverWidget
from pview.lib.patterns import KillableThread
from pyview.config.parameters import *
from pyview.lib.datacube import Datacube
from pyview.ide.mpl.canvas import MyMplCanvas
from pyview.helpers.datamanager import DataManager
from pyview.ide.editor.codeeditor import CodeEditor,globalVariables,localVariables
from pyview.lib.classes import *
from pyview.lib.smartloop import SmartLoop

class RangeViewer(QWidget,ObserverWidget):

  def resumeLoop(self):
    self._range.resume()
    print self._range.next()
    
  def stopLoop(self):
    self._range.stop()
    
  def pauseLoop(self):
    self._range.pause()

  def rewindLoop(self):
    self._range.rewind()
    
  def goBackward(self):
    self._range.goBackward()
    
  def goForward(self):
    self._range.goForward()
    
      
  def __init__(self,smartRange = None,parent = None):
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self._range = smartRange
    self._range.attach(self)
    self._canvas = MyMplCanvas(width = 5,height = 2)
    self.buttonsLayout = QBoxLayout(QBoxLayout.LeftToRight)
    
    self.resumeButton = QPushButton("Resume")
    self.stopButton = QPushButton("Stop")
    self.pauseButton = QPushButton("Pause")
    self.rewindButton = QPushButton("Rewind")
    self.backButton = QPushButton("Backward")
    self.forwardButton = QPushButton("Forward")
    
    self.buttonsLayout.addWidget(self.resumeButton)
    self.buttonsLayout.addWidget(self.stopButton)
    self.buttonsLayout.addWidget(self.pauseButton)
    self.buttonsLayout.addWidget(self.rewindButton)
    self.buttonsLayout.addWidget(self.backButton)
    self.buttonsLayout.addWidget(self.forwardButton)
    
    self.connect(self.resumeButton,SIGNAL("clicked()"),self.resumeLoop)
    self.connect(self.stopButton,SIGNAL("clicked()"),self.stopLoop)
    self.connect(self.pauseButton,SIGNAL("clicked()"),self.pauseLoop)
    self.connect(self.rewindButton,SIGNAL("clicked()"),self.rewindLoop)
    self.connect(self.backButton,SIGNAL("clicked()"),self.goBackward)
    self.connect(self.forwardButton,SIGNAL("clicked()"),self.goForward)
    
    layout = QGridLayout()
    
    self.rangeInfo = QLabel()
    
    layout.addWidget(self.rangeInfo)
    layout.addWidget(self._canvas,1,0)
    layout.addLayout(self.buttonsLayout,2,0)

    self._canvas.figure.clf()
    self._canvas.axes = self._canvas.figure.add_subplot(111)
    
    self._axline = self._canvas.axes.axvline(0)
    
    self._plot, = self._canvas.axes.plot([1,2,3])

    self._canvas.draw()

    self.setLayout(layout)

  def updatePlot(self):
    values = self._range.values()
    self._plot.set_data(range(0,len(values)),values)
    self._canvas.axes.relim()
    self._axline.remove()
    self._axline = self._canvas.axes.axvline(self._range.index())
    self._canvas.axes.autoscale_view()
    self._canvas.draw()
    
  def setRange(self,smartRange):
    if self._range != None:
      self._range.detach(self)
    self._range = smartRange
    self._range.attach(self)
    
    
  def updateView(self):
    self.updatePlot()
    if self._range.currentValue() != None:
      self.rangeInfo.setText("%s" % str(self._range.currentValue()))
    if self._range.paused():
      self.resumeButton.setEnabled(True)
      self.pauseButton.setEnabled(False)
    else:
      self.resumeButton.setEnabled(False)
      self.pauseButton.setEnabled(True)
    
  def updatedGui(self,subject,property,value = None):
    if subject == self._range:
      self.updateView()
    else:
      subject.detach(self)
      

if __name__ == '__main__':
  print PYQT_VERSION_STR 
  app = QApplication(sys.argv)

  r = SmartRange()

  MyWindow = RangeViewer(r)
  MyWindow.show()

  app.exec_()  