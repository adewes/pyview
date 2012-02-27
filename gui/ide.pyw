import sys
import os
import os.path

import random
import time
import pyview.gui.objectmodel as objectmodel
import projecttree
import yaml
import re

from PyQt4.QtGui import * 
from PyQt4.QtCore import *

from pyview.gui.editor.codeeditor import *
from pyview.gui.threadpanel import *
from pyview.gui.project import Project
from pyview.helpers.coderunner import MultiProcessCodeRunner
from pyview.gui.patterns import ObserverWidget
from pyview.config.parameters import params

class LogProxy:
  
  def __init__(self,callback):
    self._callback = callback
    
  def write(self,text):
    self._callback(text)

class Log(LineTextWidget):

    """
    Log text window.
    
    To do:
      -Add a context menu with a "clear all" menu entry
      -Add a search function
    """

    def __init__(self,parent = None ):
        LineTextWidget.__init__(self,parent)
        MyFont = QFont("Courier",10)
        MyDocument = self.document() 
        MyDocument.setDefaultFont(MyFont)
        self.setDocument(MyDocument)
        self.setMinimumHeight(200)
        self.setReadOnly(True)
        self.timer = QTimer(self)
        self._writing = False
        self.timer.setInterval(300)
        self.queuedStdoutText = ""
        self.queuedStderrText = ""
        self.connect(self.timer,SIGNAL("timeout()"),self.addQueuedText)
        self.timer.start()
        self.cnt=0
        
    def contextMenuEvent(self,event):
      MyMenu = self.createStandardContextMenu()
      MyMenu.addSeparator()
      clearLog = MyMenu.addAction("clear log")
      self.connect(clearLog,SIGNAL("triggered()"),self.clearLog)
      MyMenu.exec_(self.cursor().pos())

    def clearLog(self):
      self.clear()
        
    def addQueuedText(self): 
      if self._writing:
        return
      if self.queuedStderrText == "" and self.queuedStdoutText == "":
        return
      self.moveCursor(QTextCursor.End)
      if self.queuedStdoutText != "":
        self.textCursor().insertText(self.queuedStdoutText)
      #Insert error messages with an orange background color.
      if self.queuedStderrText != "":
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        oldFormat = cursor.blockFormat()
        format = QTextBlockFormat()
        format.setBackground(QColor(255,200,140))
        cursor.insertBlock(format)
        cursor.insertText(self.queuedStderrText)
        cursor.movePosition(QTextCursor.EndOfBlock,QTextCursor.KeepAnchor)
        cursor.setBlockFormat(oldFormat)

      self.queuedStdoutText = ""
      self.queuedStderrText = ""
        
    def writeStderr(self,text):
      while self._writing:
        time.sleep(0.1)
      try:
        self._writing = True
#        parsedText = re.sub(r'\0',r'\\0',text)
        self.queuedStderrText += text      
      finally:
        self._writing = False
        
    def writeStdout(self,text):
      while self._writing:
        time.sleep(0.1)
      try:
        self._writing = True
#        parsedText = re.sub(r'\0',r'\\0',text)
        self.queuedStdoutText += text
      finally:
        self._writing = False
        
class IDE(QMainWindow,ObserverWidget):

    """
    The main code IDE
    
    To do:
      -Add standard menu entries (edit, view, etc...)
      -Add explicit support for plugins
    """

    def fileBrowser(self):
      return self.FileBrowser

    def directory(self):
      return self.FileBrowser.directory()
      
    def saveProjectAs(self):
      filename = QFileDialog.getSaveFileName(filter = "Project (*.prj)",directory = self.workingDirectory())
      if filename != '':
        self._project.saveToFile(filename)
        self.setWorkingDirectory(filename)
        self.updateWindowTitle()
        return True
      else:
        return False

    def saveProject(self):
      if self._project.filename() != None:
        self._project.saveToFile(self._project.filename())
        self.updateWindowTitle()
        return True
      else:
        return self.saveProjectAs()

    def workingDirectory(self):
      if self._workingDirectory == None: 
        return os.getcwd()
      return self._workingDirectory
      
    def setWorkingDirectory(self,filename):
      if filename != None:
        directory = os.path.dirname(str(filename))
        self._workingDirectory = directory
      else:
        self._workingDirectory = None

    def newProject(self):
      if self._project.hasUnsavedChanges():
        MyMessageBox = QMessageBox()
        MyMessageBox.setWindowTitle("Warning!")
        MyMessageBox.setText("The current project has unsaved changed? Do you want to continue?")
        yes = MyMessageBox.addButton("Yes",QMessageBox.YesRole)
        no = MyMessageBox.addButton("No",QMessageBox.NoRole)
        MyMessageBox.exec_()
        choice = MyMessageBox.clickedButton()
        if choice == no:
          return False
      self.setProject(Project())
      return True
      
    def openProject(self,filename = None):
      if filename == None:
        filename = QFileDialog.getOpenFileName(filter = "Project (*.prj)",directory = self.workingDirectory())
      if os.path.isfile(filename):
          if self.newProject() == False:
            return False
          project = Project()
          project.loadFromFile(filename)
          self.setWorkingDirectory(filename)
          self.setProject(project)
          return True
      return False

    def closeEvent(self,e):
      self.editorWindow.closeEvent(e)
      
      if not e.isAccepted():
        return
      
      if self._project.hasUnsavedChanges():
        MyMessageBox = QMessageBox()
        MyMessageBox.setWindowTitle("Warning!")
        MyMessageBox.setText("Save changes made to your project?")
        yes = MyMessageBox.addButton("Yes",QMessageBox.YesRole)
        no = MyMessageBox.addButton("No",QMessageBox.NoRole)
        cancel = MyMessageBox.addButton("Cancel",QMessageBox.NoRole)
        MyMessageBox.exec_()
        choice = MyMessageBox.clickedButton()
        if choice == cancel:
          e.ignore()
          return
        elif choice == yes:
          if self.saveProject() == False:
            e.ignore()
            return
      settings = QSettings()
      if self._project.filename() != None:
        settings.setValue("ide.lastproject",self._project.filename())      
      else:
        settings.remove("ide.lastproject")
      settings.sync()
      self._codeRunner.terminate()
      
      ##We're saving our project...
        
    def executeCode(self,code,identifier = "main",filename = "none",editor = None):
      if self._codeRunner.executeCode(code,identifier,filename) != -1:
        self._runningCodeSessions.append((code,identifier,filename,editor))
                    
    def eventFilter(self,object,event):
      if event.type() == QEvent.KeyPress:
        if event.key() == Qt.Key_Enter and type(object) == CodeEditor:
          self.executeCode(object.getCurrentCodeBlock(),filename = object.filename() or "[unnamed buffer]",editor = object,identifier = id(object))
          return True
      return False
    
    def restartCodeProcess(self):
      self._codeRunner.restart()

      settings = QSettings()

      if settings.contains('ide.workingpath'):
        self.changeWorkingPath(str(settings.value('ide.workingpath').toString()))

    def changeWorkingPath(self,path = None):

      settings = QSettings()

      if path == None:
        path = QFileDialog.getExistingDirectory(self,"Change Working Path",directory = self.codeRunner().currentWorkingDirectory())

      if not os.path.exists(path):
        return
        
      os.chdir(str(path))
      self.codeRunner().setCurrentWorkingDirectory(str(path))

      settings.setValue("ide.workingpath",path)
      self.workingPathLabel.setText("Working path:"+path)
                      
    def setupCodeEnvironmentCallback(self,thread):
      print "Done setting up code environment..."
      
    def setupCodeEnvironment(self):
      pass
      
    def codeRunner(self):
      return self._codeRunner
      
    def terminateCodeExecution(self):
      currentEditor = self.editorWindow.currentEditor()
      for session in self._runningCodeSessions:
        (code,identifier,filename,editor) = session
        if editor == currentEditor:
          print "Stopping execution..."
          self._codeRunner.stopExecution(identifier)
          
    def onTimer(self):
      sys.stdout.write(self._codeRunner.stdout())
      sys.stderr.write(self._codeRunner.stderr())
              
    def newEditorCallback(self,editor):
      editor.installEventFilter(self)
      
    def setProject(self,project):
      self._project = project
      self.projectModel.setProject(project.tree())
      self.updateWindowTitle()
      
    def updateWindowTitle(self):
      if self._project.filename() != None:
        self.setWindowTitle(self._windowTitle+ " - " + self._project.filename())
      else:
        self.setWindowTitle(self._windowTitle)
        
    def initializeIcons(self):
      self._icons = dict()
      
      iconFilenames = {
        "newFile"             :'/actions/filenew.png',
        "openFile"            :'/actions/fileopen.png',
        "saveFile"            :'/actions/filesave.png',
        "saveFileAs"          :'/actions/filesaveas.png',
        "closeFile"           :'/actions/fileclose.png',
        "exit"                :'/actions/exit.png',
        "workingPath"         :'/actions/gohome.png',
        "killThread"          :'/actions/stop.png',
        "executeAllCode"      :'/actions/run.png',
        "executeCodeBlock"    :'/actions/kde1.png',
        "executeCodeSelection":'/actions/kde4.png',
        "logo"                :'/apps/penguin.png',
      }
      
      basePath = params['path']+params['directories.crystalIcons']
      
      for key in iconFilenames:
        self._icons[key] = QIcon(basePath+iconFilenames[key])
      
    def initializeMenus(self):
        menuBar = self.menuBar()
        
        fileMenu = menuBar.addMenu("File")
        projectMenu = menuBar.addMenu("Project")
        
        fileNew = fileMenu.addAction(self._icons["newFile"],"&New")
        fileNew.setShortcut(QKeySequence("CTRL+n"))
        fileOpen = fileMenu.addAction(self._icons["openFile"],"&Open")
        fileOpen.setShortcut(QKeySequence("CTRL+o"))
        fileClose = fileMenu.addAction(self._icons["closeFile"],"&Close")
        fileClose.setShortcut(QKeySequence("CTRL+F4"))
        fileSave = fileMenu.addAction(self._icons["saveFile"],"&Save")
        fileSave.setShortcut(QKeySequence("CTRL+s"))
        fileSaveAs = fileMenu.addAction(self._icons["saveFileAs"],"Save &As")
        fileSaveAs.setShortcut(QKeySequence("CTRL+F12"))

        projectNew = projectMenu.addAction(self._icons["newFile"],"&New")
        projectOpen = projectMenu.addAction(self._icons["openFile"],"&Open")
        projectSave = projectMenu.addAction(self._icons["saveFile"],"&Save")
        projectSaveAs = projectMenu.addAction(self._icons["saveFileAs"],"Save &As")

        fileMenu.addSeparator()

        fileExit = fileMenu.addAction(self._icons["exit"],"Exit")
        fileExit.setShortcut(QKeySequence("CTRL+ALT+F4"))
        
        self.connect(fileNew, SIGNAL('triggered()'), self.editorWindow.newEditor)
        self.connect(fileOpen, SIGNAL('triggered()'), self.editorWindow.openFile)
        self.connect(fileClose, SIGNAL('triggered()'), self.editorWindow.closeCurrentFile)
        self.connect(fileSave, SIGNAL('triggered()'), self.editorWindow.saveCurrentFile)
        self.connect(fileSaveAs, SIGNAL('triggered()'), self.editorWindow.saveCurrentFileAs)
        self.connect(fileExit, SIGNAL('triggered()'), self.close)

        self.connect(projectNew, SIGNAL('triggered()'), self.newProject)
        self.connect(projectOpen, SIGNAL('triggered()'), self.openProject)
        self.connect(projectSave, SIGNAL('triggered()'), self.saveProject)
        self.connect(projectSaveAs, SIGNAL('triggered()'), self.saveProjectAs)
        
        fileMenu.addSeparator()  

        self.editMenu = menuBar.addMenu("Edit")
        self.viewMenu = menuBar.addMenu("View")

        self.toolsMenu = menuBar.addMenu("Tools")
        self.codeMenu = menuBar.addMenu("Code")
        self.settingsMenu = menuBar.addMenu("Settings")
        self.windowMenu = menuBar.addMenu("Window")
        self.helpMenu = menuBar.addMenu("Help")
        
        restartCodeRunner = self.codeMenu.addAction("Restart Code Process")
        
        self.connect(restartCodeRunner,SIGNAL("triggered()"),self.restartCodeProcess)      

    def initializeToolbars(self):
        self.mainToolbar = self.addToolBar("Tools")

        icons = self._icons

        newFile = self.mainToolbar.addAction(icons["newFile"],"New")
        openFile = self.mainToolbar.addAction(icons["openFile"],"Open")
        saveFile = self.mainToolbar.addAction(icons["saveFile"],"Save")
        saveFileAs = self.mainToolbar.addAction(icons["saveFileAs"],"Save As")

        self.mainToolbar.addSeparator()
                
        executeAll = self.mainToolbar.addAction(icons["executeAllCode"],"Run")
        executeBlock = self.mainToolbar.addAction(icons["executeCodeBlock"],"Run Block")
        executeSelection = self.mainToolbar.addAction(icons["executeCodeSelection"],"Run Selection")

        self.mainToolbar.addSeparator()

        changeWorkingPath = self.mainToolbar.addAction(self._icons["workingPath"],"Change working path")
        killThread = self.mainToolbar.addAction(self._icons["killThread"],"Kill Thread")
        
        self.connect(executeBlock,SIGNAL('triggered()'),lambda: self.executeCode(self.editorWindow.currentEditor().getCurrentCodeBlock(),filename = self.editorWindow.currentEditor().filename() or "[unnamed buffer]",editor = self.editorWindow.currentEditor(),identifier = id(self.editorWindow.currentEditor())))
        
        self.connect(newFile, SIGNAL('triggered()'), self.editorWindow.newEditor)
        self.connect(openFile, SIGNAL('triggered()'), self.editorWindow.openFile)
        self.connect(saveFile, SIGNAL('triggered()'), self.editorWindow.saveCurrentFile)
        self.connect(saveFileAs, SIGNAL('triggered()'), self.editorWindow.saveCurrentFileAs)
        self.connect(killThread,SIGNAL("triggered()"),self.terminateCodeExecution)
        self.connect(changeWorkingPath, SIGNAL('triggered()'), self.changeWorkingPath)

    def __init__(self,parent=None):
        QMainWindow.__init__(self,parent)
        ObserverWidget.__init__(self)
        
        self._timer = QTimer(self)
        self._runningCodeSessions = []
        self._timer.setInterval(500)
        self.connect(self._timer,SIGNAL("timeout()"),self.onTimer)
        self._timer.start()
        
        self._windowTitle = "Python Lab IDE"
        self._workingDirectory = None
        self.setWindowTitle(self._windowTitle)
        
        self.setDockOptions(QMainWindow.AllowTabbedDocks)
        self.LeftBottomDock = QDockWidget()
        self.RightBottomDock = QDockWidget()
        self.LeftBottomDock.setWindowTitle("Log")
        self.RightBottomDock.setWindowTitle("File Browser")

        self.MyLog = Log()
        
        horizontalSplitter = QSplitter(Qt.Horizontal)
        verticalSplitter = QSplitter(Qt.Vertical)      

        gv = dict()

        self._codeRunner = MultiProcessCodeRunner(gv = gv,lv = gv)

        self.editorWindow = CodeEditorWindow(self,newEditorCallback = self.newEditorCallback)
        self.errorConsole = ErrorConsole(codeEditorWindow = self.editorWindow,codeRunner = self._codeRunner)
        
        self.tabs = QTabWidget()
        self.logTabs = QTabWidget()
        
        self.logTabs.addTab(self.MyLog,"Log")
        self.logTabs.addTab(self.errorConsole,"Traceback")
        
        self.tabs.setMaximumWidth(350)
        horizontalSplitter.addWidget(self.tabs)
        horizontalSplitter.addWidget(self.editorWindow)
        verticalSplitter.addWidget(horizontalSplitter)
        verticalSplitter.addWidget(self.logTabs)
        verticalSplitter.setStretchFactor(0,2)        
        
        self.projectWindow = QWidget()        
                
        self.projectTree = projecttree.ProjectView() 
        self.projectModel = projecttree.ProjectModel(objectmodel.Folder("[project]"))
        self.projectTree.setModel(self.projectModel)
        self.projectToolbar = QToolBar()
        
        newFolder = self.projectToolbar.addAction("New Folder")
        edit = self.projectToolbar.addAction("Edit")
        delete = self.projectToolbar.addAction("Delete")
        
        self.connect(newFolder,SIGNAL("triggered()"),self.projectTree.createNewFolder)
        self.connect(edit,SIGNAL("triggered()"),self.projectTree.editCurrentItem)
        self.connect(delete,SIGNAL("triggered()"),self.projectTree.deleteCurrentItem)

        layout = QGridLayout()
        layout.addWidget(self.projectToolbar)
        layout.addWidget(self.projectTree)
        
        self.projectWindow.setLayout(layout)
        
        self.threadPanel = ThreadPanel(codeRunner = self._codeRunner,editorWindow = self.editorWindow)
        
        self.tabs.addTab(self.projectWindow,"Project")        
        self.tabs.addTab(self.threadPanel,"Processes")
        self.connect(self.projectTree,SIGNAL("openFile(PyQt_PyObject)"),lambda filename: self.editorWindow.openFile(filename))

        StatusBar = self.statusBar()
        self.workingPathLabel = QLabel("Working path: ?")
        StatusBar.addWidget(self.workingPathLabel)  

        self.setCentralWidget(verticalSplitter)
        
        self.initializeIcons()
        self.initializeMenus()
        self.initializeToolbars()
        
        self.setWindowIcon(self._icons["logo"])
        
        #We add a timer
        self.queuedText = ""
        
                
        self.errorProxy = LogProxy(self.MyLog.writeStderr)
        self.eventProxy = LogProxy(self.MyLog.writeStdout)

        settings = QSettings()

        if settings.contains('ide.workingpath'):
          self.changeWorkingPath(settings.value('ide.workingpath').toString())

        self.setProject(Project())
        
        if settings.contains("ide.lastproject"):
          try:
            self.openProject(str(settings.value("ide.lastproject").toString()))
          except:
            print "Cannot open last project: %s " % str(settings.value("ide.lastproject").toString())
        
        sys.stdout = self.eventProxy
        sys.stderr = self.errorProxy

        self.logTabs.show()
        


def startIDE(qApp = None):
  if qApp == None:
    qApp = QApplication(sys.argv)

  QCoreApplication.setOrganizationName("Andreas Dewes")
  QCoreApplication.setOrganizationDomain("cea.fr")
  QCoreApplication.setApplicationName("Python Code IDE")

  qApp.setStyle(QStyleFactory.create("QMacStyle"))
  qApp.setStyleSheet("""
QTreeWidget:Item {padding:6;}
QTreeView:Item {padding:6;}
  """)
  qApp.connect(qApp, SIGNAL('lastWindowClosed()'), qApp,
                    SLOT('quit()'))
  MyIDE = IDE()
  MyIDE.showMaximized()
  qApp.exec_()
  
if __name__ == '__main__':
  startIDE()
