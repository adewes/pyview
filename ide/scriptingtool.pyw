import sys
import getopt

sys.path.append('.')
sys.path.append('../')

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtWebKit import *
from pyview.ide.preferences import *
import pickle
import cPickle
import copy


from pyview.lib.patterns import ObserverWidget,KillableThread
from pyview.conf.parameters import *
from pyview.lib.datacube import Datacube
from pyview.helpers.datamanager import DataManager
from pyview.ide.codeeditor import CodeEditor,globalVariables,localVariables
from pyview.lib.classes import *


import pyview.ide.mpl.backend_agg as mpl_backend

class ScriptingTool(QMainWindow,ObserverWidget):

  def __init__(self,parent = None):
    QMainWindow.__init__(self,parent)
    ObserverWidget.__init__(self)
    
    self.setAttribute(Qt.WA_DeleteOnClose,True)
  
    self.preferences = Preferences(filename = "scriptingtool")
  
    self.scripts = dict()
    
    self.setWindowTitle("Scripting Tool")
    self.setMinimumSize(800,600)
  

    self.savedScripts = QComboBox()
    self.savedScripts.setMinimumContentsLength(50)
    self.savedScripts.setEditable(True)
    self.removeButton = QPushButton("Remove")
    self.newButton = QPushButton("New")
    self.loadButton = QPushButton("Load")
    self.scriptTabs = QTabWidget()

    self.scriptTabs.setTabsClosable(True)

    self.saveButton = QPushButton("Save")

    self.connect(self.newButton,SIGNAL("clicked()"),self.newScript)
    self.connect(self.scriptTabs,SIGNAL("tabCloseRequested(int)"),self.closeTab)
    self.connect(self.saveButton,SIGNAL("clicked()"),self.saveScript)
    self.connect(self.loadButton,SIGNAL("clicked()"),self.loadScript)
    self.connect(self.removeButton,SIGNAL("clicked()"),self.deleteScript)
    self.connect(self.scriptTabs,SIGNAL("currentChanged(int)"),self.setScriptNameFromTabName)

    saveLayout = QBoxLayout(QBoxLayout.LeftToRight)
    saveLayout.addWidget(self.savedScripts)
    saveLayout.addWidget(self.newButton)
    saveLayout.addWidget(self.loadButton)
    saveLayout.addWidget(self.removeButton)
    saveLayout.addWidget(self.saveButton)
    saveLayout.addStretch()
        
    widget = QWidget()
    
    layout = QGridLayout()
    layout.addLayout(saveLayout,0,0)
    layout.addWidget(self.scriptTabs,1,0)

    widget.setLayout(layout)
    
    self.setCentralWidget(widget)
    
    self.loadScripts()
    self.updateScripts()
    
    self.restore()

  def setScriptNameFromTabName(self,i):
    self.savedScripts.setEditText(self.scriptTabs.tabText(i))
    
  def setScriptNameFromListName(self,current,previous):
    if current != None:
      self.savedScripts.setEditText(current.text())

  def save(self):
    scripts = []
    for i in range(0,self.scriptTabs.count()):
      script = self.scriptTabs.widget(i)    
      scripts.append(script.save())
    self.preferences.set("scriptingTool.scripts",scripts)
    self.preferences.save() 
    
  def restore(self):
    try:
      scripts = self.preferences.get("scriptingTool.scripts")
      if scripts == None:
        return
      for script in scripts:
        widget = self.newScript(script["name"])
        widget.load(script)
    except KeyError:
      print sys.exc_info()
      print "Error"
      pass

  def closeEvent(self,e):
    print "Closing..."
    self.save()
    QMainWindow.closeEvent(self,e) 

  def closeTab(self,index):
    window = self.scriptTabs.widget(index)
    if window.close():
      window.destroy()
      self.scriptTabs.removeTab(index)
      if self.scriptTabs.count() == 0:
        self.newScript()

  def newScript(self,name = "unnamed"):
    script = ScriptWidget()
    self.scriptTabs.addTab(script,name)
    self.scriptTabs.setCurrentWidget(script)
    return script

  def loadScripts(self,filename = "scripts.dat"):
    try:
      f = open(params['path']+"/"+filename,"r")
    except IOError:
      print "Cannot open file!"
      return
    c = f.read()
    try:
      self.scripts = pickle.loads(c)
    except:
      self.scripts = dict()
    
  def activeScript(self):
    script = self.scriptTabs.widget(self.scriptTabs.currentIndex())
    return script
    
  def deleteScript(self):
    name = str(self.savedScripts.currentText())
    if name in self.scripts:
      message = QMessageBox( )
      message.setWindowTitle("Confirm Script Deletion")
      message.setIcon(QMessageBox.Question) 
      message.setText("Do you really want to remove the script \"%s\"?" % name)
      message.setStandardButtons(QMessageBox.Cancel  | QMessageBox.Ok)
      message.setDefaultButton(QMessageBox.Cancel)
      result = message.exec_()
      if result == QMessageBox.Cancel:
        return
      del self.scripts[name]
      self.savedScripts.removeItem(self.savedScripts.findText(name,Qt.MatchExactly))
      self.saveScripts()
    
  def saveScript(self):
    script = self.activeScript()
    name = str(self.savedScripts.currentText())
    self.scripts[name] = script.save()
    self.saveScripts()
    self.updateScripts()
    self.savedScripts.setCurrentIndex(self.savedScripts.findText(name,Qt.MatchExactly))
    self.scriptTabs.setTabText(self.scriptTabs.currentIndex(),name)
    script.setName(name)
    
  def loadScript(self):
    name = str(self.savedScripts.currentText())
    if name in self.scripts.keys():
      print "Loading %s" %  name
      script = self.newScript(name)
      script.load(self.scripts[name])


  def saveScripts(self,filename = "scripts.dat"):
    try:
      f = open(params['path']+"/"+filename,"w")
    except IOError:
      print "Cannot open file!"
      return
    f.write(pickle.dumps(self.scripts))
    f.close()

  def updateScripts(self):
    self.savedScripts.clear()
    for script in self.scripts.keys():
      self.savedScripts.addItem(script)
    

class ScriptWidget(QWidget,ObserverWidget):

  def onTimer(self):
    if self._codeFinished:
      self.runButton.setEnabled(True)
      self.stopButton.setEnabled(False)
      
  def name(self):
    return self._name
    
  def setName(self,name):
    self._name = name
    
  def codeFinished(self,thread):
    self._codeFinished = True
  
  def runScript(self):
    self._codeFinished = False
    self.code.executeAll(callback = self.codeFinished)
    self.runButton.setEnabled(False)
    self.stopButton.setEnabled(True)
        
  def resumeScript(self):
    pass
  
  def pauseScript(self):
    pass
        
  def stopScript(self):
    self.code.killThread()
    self.runButton.setEnabled(True)
    self.resumeButton.setEnabled(False)
  
  def save(self):
    params = dict()
    params["code"] = self.code.toPlainText()
    params["name"] = self._name
    return params
    
  def load(self,params):
    self.code.setPlainText(params["code"])
    
  def updatedGui(self,subject,property,value):
    pass
        
  def __init__(self,parent = None):
    global params
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self.timer = QTimer(self)
    self._codeFinished = False
    self._name = "undefined"
    self.timer.setInterval(1000)
    self.timer.start()
    
    
    self.code = CodeEditor()
    
    
    self.runButton = QPushButton("Run")
    self.pauseButton = QPushButton("Pause")
    self.resumeButton = QPushButton("Resume")
    self.stopButton = QPushButton("Stop")
    
    
    layout = QGridLayout()
    
    buttonsLayout = QBoxLayout(QBoxLayout.LeftToRight)
    
    buttonsLayout.addWidget(self.runButton)
#    buttonsLayout.addWidget(self.pauseButton)
#    buttonsLayout.addWidget(self.resumeButton)
    buttonsLayout.addWidget(self.stopButton)
    buttonsLayout.addStretch()
        
    codeLayout = QGridLayout()
    
    codeLayout.addWidget(QLabel("Code"))
    codeLayout.addWidget(self.code)
    
    layout.addItem(buttonsLayout,0,0,1,2)
    layout.addItem(codeLayout,1,0)
    
    layout.setColumnStretch(0,1)
    layout.setColumnStretch(1,0)
    
    self.connect(self.timer,SIGNAL("timeout()"),self.onTimer)
    self.connect(self.runButton,SIGNAL("clicked()"),self.runScript)
    self.connect(self.stopButton,SIGNAL("clicked()"),self.stopScript)
#    self.connect(self.pauseButton,SIGNAL("clicked()"),self.pauseScript)
#    self.connect(self.resumeButton,SIGNAL("clicked()"),self.resumeScript)

    self.code.activateHighlighter()
    self.preferences = Preferences()
    self.setAttribute(Qt.WA_DeleteOnClose,True)
    self.setLayout(layout)
    