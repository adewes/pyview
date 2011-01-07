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


from pyview.lib.patterns import ObserverWidget,KillableThread
if 'pyview.lib.ramps' in sys.modules:
  reload(sys.modules['pyview.lib.ramps'])
from pyview.lib.ramps import *
from pyview.conf.parameters import *
from pyview.lib.datacube import Datacube
from pyview.helpers.datamanager import DataManager
from pyview.ide.codeeditor import CodeEditor,globalVariables,localVariables
from pyview.lib.classes import *


import pyview.ide.mpl.backend_agg as mpl_backend

class RampThread(KillableThread):

  def __init__(self,ramp,datacube,gv = globals(),lv = globals()):
    KillableThread.__init__(self)
    self.ramp = ramp
    self.datacube = datacube
    self.gv = gv
    self.lv = lv    
  def run(self):
    if self.ramp == None:
      return
    self.ramp.run(self.datacube,gv = self.gv,lv = self.lv)

class MeasurementExplorer(QMainWindow,ObserverWidget):

  def __init__(self,parent = None):
    QMainWindow.__init__(self,parent)
    ObserverWidget.__init__(self)
    
    self.setAttribute(Qt.WA_DeleteOnClose,True)
  
    self.preferences = Preferences(filename = "measurementexplorer")
  
    self.measurements = dict()
    
    self.setWindowTitle("Measurement Tool")
    self.setMinimumSize(800,600)
  

    self.measurementTree = QTreeView()

    self.connect(self.newButton,SIGNAL("clicked()"),self.newMeasurement)
    self.connect(self.measurementTabs,SIGNAL("tabCloseRequested(int)"),self.closeTab)
    self.connect(self.saveButton,SIGNAL("clicked()"),self.saveMeasurement)
    self.connect(self.loadButton,SIGNAL("clicked()"),self.loadMeasurement)
    self.connect(self.removeButton,SIGNAL("clicked()"),self.deleteMeasurement)
#    self.connect(self.measurementTabs,SIGNAL("currentChanged(int)"),self.setMeasurementNameFromTabName)

    saveLayout = QBoxLayout(QBoxLayout.LeftToRight)
    saveLayout.addWidget(self.savedMeasurements)
    saveLayout.addWidget(self.newButton)
    saveLayout.addWidget(self.loadButton)
    saveLayout.addWidget(self.removeButton)
    saveLayout.addWidget(self.saveButton)
    saveLayout.addStretch()
        
    widget = QWidget()
    
    layout = QGridLayout()
    layout.addLayout(saveLayout,0,0)
    layout.addWidget(self.measurementTabs,1,0)

    widget.setLayout(layout)
    
    self.setCentralWidget(widget)
    
    self.loadMeasurements()
    self.updateMeasurements()
    
    self.restore()

  def setMeasurementNameFromTabName(self,i):
    self.savedMeasurements.setEditText(self.measurementTabs.tabText(i))
    
  def setMeasurementNameFromListName(self,current,previous):
    if current != None:
      self.savedMeasurements.setEditText(current.text())

  def save(self):
    print "Saving measurements..."
    measurements = []
    for i in range(0,self.measurementTabs.count()):
      measurement = self.measurementTabs.widget(i)    
      measurements.append(measurement.save())
    self.preferences.set("measurementTool.ramps",measurements)
    self.preferences.save() 
    
  def restore(self):
    try:
      measurements = self.preferences.get("measurementTool.ramps")
      if measurements == None:
        return
      for measurement in measurements:
        widget = self.newMeasurement(measurement["name"])
        widget.load(measurement)
    except KeyError:
      print sys.exc_info()
      print "Error"
      pass

  def closeEvent(self,e):
    print "Closing..."
    self.save()
    QMainWindow.closeEvent(self,e) 

  def closeTab(self,index):
    window = self.measurementTabs.widget(index)
    if window.close():
      window.destroy()
      self.measurementTabs.removeTab(index)
      if self.measurementTabs.count() == 0:
        self.newMeasurement()

  def newMeasurement(self,name = "unnamed"):
    measurement = MeasurementWidget()
    self.measurementTabs.addTab(measurement,name)
    self.measurementTabs.setCurrentWidget(measurement)
    return measurement

  def loadMeasurements(self,filename = "measurements.dat"):
    try:
      global params
      f = open(params['directories.setup']+"/config/"+filename,"r")
    except IOError:
      print "Cannot open file!"
      return
    c = f.read()
    try:
      self.measurements = pickle.loads(c)
    except:
      self.measurements = dict()
    
  def activeMeasurement(self):
    measurement = self.measurementTabs.widget(self.measurementTabs.currentIndex())
    return measurement
    
  def deleteMeasurement(self):
    name = str(self.savedMeasurements.currentText())
    if name in self.measurements:
      message = QMessageBox( )
      message.setWindowTitle("Confirm Measurement Deletion")
      message.setIcon(QMessageBox.Question) 
      message.setText("Do you really want to remove the measurement \"%s\"?" % name)
      message.setStandardButtons(QMessageBox.Cancel  | QMessageBox.Ok)
      message.setDefaultButton(QMessageBox.Cancel)
      result = message.exec_()
      if result == QMessageBox.Cancel:
        return
      del self.measurements[name]
      self.savedMeasurements.removeItem(self.savedMeasurements.findText(name,Qt.MatchExactly))
      self.saveMeasurements()
    
  def saveMeasurement(self):
    measurement = self.activeMeasurement()
    name = str(self.savedMeasurements.currentText())
    self.measurements[name] = measurement.save()
    self.saveMeasurements()
    self.updateMeasurements()
    self.savedMeasurements.setCurrentIndex(self.savedMeasurements.findText(name,Qt.MatchExactly))
    self.measurementTabs.setTabText(self.measurementTabs.currentIndex(),name)
    measurement.setName(name)
    
  def loadMeasurement(self):
    name = str(self.savedMeasurements.currentText())
    if name in self.measurements.keys():
      print "Loading %s" %  name
      measurement = self.newMeasurement(name)
      measurement.load(self.measurements[name])


  def saveMeasurements(self,filename = "measurements.dat"):
    try:
      f = open(params['directories.setup']+"/config/"+filename,"w")
    except IOError:
      print "Cannot open file!"
      return
    f.write(pickle.dumps(self.measurements))
    f.close()

  def updateMeasurements(self):
    self.savedMeasurements.clear()
    for measurement in self.measurements.keys():
      self.savedMeasurements.addItem(measurement)
    

class MeasurementWidget(QWidget,ObserverWidget):
  
  def addRamp(self):
    ramptree = self.rampTree
    item = QTreeWidgetItem() 
    ramp = ParameterRamp()
    item.ramp = ramp
    item.setText(0,ramp.name())
    selectedItem = ramptree.currentItem()
    if not selectedItem == None:
      selectedItem.addChild(item)
      selectedItem.ramp.addChild(ramp)

  def updateRampInfo(self):
    selectedItems = self.rampTree.selectedItems()
    if len(selectedItems) > 0:
      item = selectedItems[0]
      ramp = item.ramp
      self.currentItem = item
      self.currentRamp = ramp
      self.rampGenerator.setPlainText(ramp.generator())
      self.rampCode.setPlainText(ramp.code())
      self.rampFinish.setPlainText(ramp.finish())
      self.rampName.setText(ramp.name())
    else:
      self.currentRamp = None
      self.rampGenerator.setPlainText("")
      self.rampCode.setPlainText("")
      self.rampFinish.setPlainText("")

  def onTimer(self):
    pass
      
  def name(self):
    return self._name
    
  def setName(self,name):
    self._name = name
      
  def deleteRamp(self):
    ramptree = self.rampTree
    selectedItem = ramptree.currentItem()
    if not selectedItem == None:
      parent = selectedItem.parent()
      if not parent == None:
        parent.removeChild(selectedItem)
        parent.ramp.removeChild(selectedItem.ramp)
    
  def initRampTree(self):
    self.rampTree.clear()
    item = QTreeWidgetItem()
    item.ramp = self.root
    self.root.attach(self)
    item.setText(0,self.root.name())
    if self.root == None:
      self.root = item.ramp
    self.rampTree.insertTopLevelItem(0,item)
        
    def addChildren(ramp,item):
      for child in ramp.children():
        subitem = QTreeWidgetItem()
        subitem.setText(0,child.name())
        subitem.ramp = child
        item.addChild(subitem)
        addChildren(child,subitem)

    addChildren(self.root,item)
    
    item.setSelected(True)
  
  def updateRampStatus(self):
    if self.root.isRunning() and not self.root.isPaused():
      self.runButton.setEnabled(False)
      self.resumeButton.setEnabled(False)
      self.pauseButton.setEnabled(True)
      self.stopButton.setEnabled(True)
    elif self.root.isPaused():#The ramped is paused.
      self.resumeButton.setEnabled(True)
      self.pauseButton.setEnabled(False)
    else:#The ramp is stopped.
      self.runButton.setEnabled(True)
      self.resumeButton.setEnabled(False)
      self.pauseButton.setEnabled(False)
      self.stopButton.setEnabled(False)

  
  def updateRampProperty(self,property = None,all = False):
    if self.currentRamp == None:
      return
    if self.root.isRunning() and not self.root.isPaused():
      return
    if property == "code" or all:
      self.currentRamp.setCode(self.rampCode.toPlainText())
    if property == "finish" or all:
      self.currentRamp.setFinish(self.rampFinish.toPlainText())
    elif property == "generator" or all:
      self.currentRamp.setGenerator(self.rampGenerator.toPlainText())
    elif property == "name" or all:
      self.currentRamp.setName(self.rampName.text())
      self.currentItem.setText(0,self.currentRamp.name())
     
  def runRamps(self):
    if self.root == None:
      return
    if hasattr(self,'rampThread'):
      if self.rampThread.isAlive():
        return
    cube = Datacube()
    manager = DataManager()
    self.updateRampProperty(all = True)
    print "Running..."
    manager.addDatacube(cube)
    self.rampThread = RampThread(self.root,cube,globalVariables,globalVariables)
    self.rampThread.start()        
        
  def resumeRamps(self):
    if self.root == None:
      return
    self.root.fullResume()  
  
  def pauseRamps(self):
    if self.root == None:
      return
    self.root.fullPause()
    
  def stopRamps(self):
    if self.root == None:
      return
    print "Stopping ramp!"
    self.root.fullStop()    
  
  def save(self):
    params = dict()
    params["root"] = self.root.dump()
    params["name"] = self._name
    return params
    
  def load(self,params):
    self.root = ParameterRamp()
    self.root.load(params["root"])
    if "name" in params:
      self.setName(params["name"])
    self.initRampTree()
    
  def updatedGui(self,subject,property,value):
    if subject == self.root:
      self.updateRampStatus()
        
  def __init__(self,ramp,parent = None):
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self.currentRamp = None
    self.root = ParameterRamp()
    self.measurements = dict()
    self.timer = QTimer(self)
    self._name = "undefined"
    self.timer.setInterval(1000)
    self.timer.start()
    
    
    self.rampCode = CodeEditor()
    self.rampGenerator = CodeEditor()
    self.rampFinish = CodeEditor()

    layout = QGridLayout()
    
    codeLayout = QGridLayout()
    
    codeLayout.addWidget(QLabel("Initialization code (will be executed before the ramp is executed)"))
    codeLayout.addWidget(self.rampGenerator)
    codeLayout.addWidget(QLabel("Measurement code (will be executed at each point of the ramp)"))
    codeLayout.addWidget(self.rampCode)
    codeLayout.addWidget(QLabel("Finish (will be executed after the ramp has finished or has been stopped)"))
    codeLayout.addWidget(self.rampFinish)
    
    layout.addItem(codeLayout,1,0)
    
    self.connect(self.timer,SIGNAL("timeout()"),self.onTimer)
    self.connect(self.rampCode,SIGNAL("textChanged()"),lambda property = "code":self.updateRampProperty(property))
    self.connect(self.rampFinish,SIGNAL("textChanged()"),lambda property = "finish":self.updateRampProperty(property))
    self.connect(self.rampGenerator,SIGNAL("textChanged()"),lambda property = "generator":self.updateRampProperty(property))
    self.connect(self.rampName,SIGNAL("textEdited(QString)"),lambda string,property = "name":self.updateRampProperty(property))

    self.rampCode.activateHighlighter()
    self.rampFinish.activateHighlighter()
    self.rampGenerator.activateHighlighter()    
    self.preferences = Preferences()
    self.setAttribute(Qt.WA_DeleteOnClose,True)
    self.initRampTree()
    self.updateRampStatus()
    self.setLayout(layout)
    