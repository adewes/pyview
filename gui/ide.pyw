import sys
import os
import os.path

import random
import time
import objectmodel
import projecttree
import yaml
import re

from PyQt4.QtGui import * 
from PyQt4.QtCore import *

from pyview.gui.editor.codeeditor import *
from pyview.gui.threadpanel import *
from pyview.helpers.coderunner import MultiProcessCodeRunner
from pyview.ide.patterns import ObserverWidget
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

    def closeEvent(self,e):
      MyMessageBox = QMessageBox()
      MyMessageBox.setWindowTitle("Warning!")
      MyMessageBox.setText("Do you really want to close the IDE?")
      yes = MyMessageBox.addButton("Yes",QMessageBox.YesRole)
      no = MyMessageBox.addButton("No",QMessageBox.NoRole)
      MyMessageBox.exec_()
      choice = MyMessageBox.clickedButton()
      if choice == no:
        e.ignore()
        return
      self.Editor.closeEvent(e)
      self.projectTree.saveToSettings()
      self._codeRunner.terminate()
        
    def executeCode(self,code,identifier = "main",filename = "none",editor = None):
      if self._codeRunner.executeCode(code,identifier,filename) != -1:
        self._runningCodeSessions.append((code,identifier,filename,editor))
        if editor != None:
          editor.updateTab(running = True)
            
    def eventFilter(self,object,event):
      if event.type() == QEvent.KeyPress:
        if event.key() == Qt.Key_Enter and type(object) == CodeEditor:
          self.executeCode(object.getCurrentCodeBlock(),filename = object.filename() or "[undefined filename]",editor = object,identifier = id(object))
          return True
      return False

    def changeWorkingPath(self,path = None):

      settings = QSettings()

      if path == None:
        path = QFileDialog.getExistingDirectory(self,"Change Working Path")
      if not os.path.exists(path):
        return
      os.chdir(unicode(path)) 
      
      settings.setValue("IDE/WorkingPath",path)
      
      self.workingPathLabel.setText("Working path:"+os.getcwd())
                      
    def setupCodeEnvironmentCallback(self,thread):
      print "Done setting up code environment..."
      
    def setupCodeEnvironment(self):
      pass
      
    def codeRunner(self):
      return self._codeRunner
      
    def terminateCodeExecution(self):
      currentEditor = self.Editor.currentEditor()
      for session in self._runningCodeSessions:
        (code,identifier,filename,editor) = session
        if editor == currentEditor:
          print "Stopping execution..."
          self._codeRunner.stopExecution(identifier)
          
    def onTimer(self):
      for session in self._runningCodeSessions:
        (code,identifier,filename,editor) = session
        if self._codeRunner.isExecutingCode(identifier):
          if editor != None:
            editor.updateTab(running = True)
          pass
        else:
          if self._codeRunner.hasFailed(identifier):
            if editor != None:
              editor.updateTab(failed = True,running = False)
          else:
            if editor != None:
              editor.updateTab(running = False,failed = False)
          del self._runningCodeSessions[self._runningCodeSessions.index(session)]
      sys.stdout.write(self._codeRunner.stdout())
      sys.stderr.write(self._codeRunner.stderr())
      
    def openFile(self,filename):
      self.Editor.openFile(filename)

    def __init__(self,parent=None):
        QMainWindow.__init__(self,parent)
        ObserverWidget.__init__(self)
        
        self._timer = QTimer(self)
        self._runningCodeSessions = []
                               
        self._timer.setInterval(500)
        
        self.connect(self._timer,SIGNAL("timeout()"),self.onTimer)
        
        self._timer.start()
        
        self.setWindowTitle("Python Lab IDE, A. Dewes")
        
        
        self.setDockOptions(QMainWindow.AllowTabbedDocks	)

        self.LeftBottomDock = QDockWidget()
        self.RightBottomDock = QDockWidget()
                
          
        self.LeftBottomDock.setWindowTitle("Log")
        self.RightBottomDock.setWindowTitle("File Browser")

        self.MyLog = Log()
        
        horizontalSplitter = QSplitter(Qt.Horizontal)
        verticalSplitter = QSplitter(Qt.Vertical)      

        gv = dict()

        self._codeRunner = MultiProcessCodeRunner(gv = gv,lv = gv)

        self.Editor = CodeEditorWindow(self,ide = self)
        self.errorConsole = ErrorConsole(codeEditorWindow = self.Editor,codeRunner = self._codeRunner)
        
        self.tabs = QTabWidget()
        self.logTabs = QTabWidget()
        
        self.logTabs.addTab(self.MyLog,"Log")
        self.logTabs.addTab(self.errorConsole,"Traceback")
        
        self.tabs.setMaximumWidth(350)
        horizontalSplitter.addWidget(self.tabs)
        horizontalSplitter.addWidget(self.Editor)
        verticalSplitter.addWidget(horizontalSplitter)
        verticalSplitter.addWidget(self.logTabs)
        verticalSplitter.setStretchFactor(0,2)        
        
        self.projectWindow = QWidget()        
        
        node = objectmodel.Folder("[project]")
        node.addChild(objectmodel.Folder("experiment"))
        node.addChild(objectmodel.Folder("theory"))
        
        self.projectTree = projecttree.ProjectView() 
        self.projectModel = projecttree.ProjectModel(node)
        self.projectTree.setModel(self.projectModel)
        self.projectToolbar = QToolBar()
        
        newFolder = self.projectToolbar.addAction("New Folder")
        edit = self.projectToolbar.addAction("Edit")
        delete = self.projectToolbar.addAction("Delete")
        
#        self.connect(newFolder,SIGNAL("triggered()"),self.projectTree.createNewFolder)
#        self.connect(edit,SIGNAL("triggered()"),self.projectTree.editCurrentItem)
#        self.connect(delete,SIGNAL("triggered()"),self.projectTree.deleteCurrentItem)

        layout = QGridLayout()
        layout.addWidget(self.projectToolbar)
        layout.addWidget(self.projectTree)
        
        self.projectWindow.setLayout(layout)
        
        self.threadPanel = ThreadPanel()
        
        self.tabs.addTab(self.projectWindow,"Project")        
        self.tabs.addTab(self.threadPanel,"Processes")
        self.connect(self.projectTree,SIGNAL("openFile(PyQt_PyObject)"),self.openFile)

        StatusBar = self.statusBar()
        self.workingPathLabel = QLabel("Working path: ?")
        StatusBar.addWidget(self.workingPathLabel)  

        self.setCentralWidget(verticalSplitter)
        
        self.MyMenuBar = self.menuBar()
                
        FileMenu = self.MyMenuBar.addMenu("File")
        
        newIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/filenew.png')
        openIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/fileopen.png')
        saveIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/filesave.png')
        saveAsIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/filesaveas.png')
        closeIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/fileclose.png')
        exitIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/exit.png')
        workingPathIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/gohome.png')
        killThreadIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/stop.png')
        
        fileNew = FileMenu.addAction(newIcon,"&New")
        fileNew.setShortcut(QKeySequence("CTRL+n"))
        fileOpen = FileMenu.addAction(openIcon,"&Open")
        fileOpen.setShortcut(QKeySequence("CTRL+o"))
        fileClose = FileMenu.addAction(closeIcon,"&Close")
        fileClose.setShortcut(QKeySequence("CTRL+F4"))
        fileSave = FileMenu.addAction(saveIcon,"&Save")
        fileSave.setShortcut(QKeySequence("CTRL+s"))
        fileSaveAs = FileMenu.addAction(saveAsIcon,"Save &As")
        fileSaveAs.setShortcut(QKeySequence("CTRL+F12"))

        FileMenu.addSeparator()

        fileExit = FileMenu.addAction(exitIcon,"Exit")
        fileExit.setShortcut(QKeySequence("CTRL+ALT+F4"))
        
        self.connect(fileNew, SIGNAL('triggered()'), self.Editor.newEditor)
        self.connect(fileOpen, SIGNAL('triggered()'), self.Editor.openFile)
        self.connect(fileClose, SIGNAL('triggered()'), lambda : self.Editor.closeTab(self.Editor.Tab.currentIndex()))
        self.connect(fileSave, SIGNAL('triggered()'), lambda : self.Editor.Tab.currentWidget().saveFile())
        self.connect(fileSaveAs, SIGNAL('triggered()'), lambda : self.Editor.Tab.currentWidget().saveFileAs())
        self.connect(fileExit, SIGNAL('triggered()'), self.close)

        
        FileMenu.addSeparator()  

        self.editMenu = self.MyMenuBar.addMenu("Edit")
        self.viewMenu = self.MyMenuBar.addMenu("View")

        showLog = self.viewMenu.addAction("Show Log")
        self.connect(showLog,SIGNAL("triggered()"),lambda :self.logTabs.show())

        self.toolsMenu = self.MyMenuBar.addMenu("Tools")
        self.settingsMenu = self.MyMenuBar.addMenu("Settings")
        self.windowMenu = self.MyMenuBar.addMenu("Window")
        self.helpMenu = self.MyMenuBar.addMenu("Help")
        self.MyToolbar = self.addToolBar("Tools")
        
        newFile = self.MyToolbar.addAction(newIcon,"New")
        openFile = self.MyToolbar.addAction(openIcon,"Open")
        saveFile = self.MyToolbar.addAction(saveIcon,"Save")
        saveFileAs = self.MyToolbar.addAction(saveAsIcon,"Save As")

        self.MyToolbar.addSeparator()
                
        executeAll = self.MyToolbar.addAction(QIcon(params['path']+params['directories.crystalIcons']+'/actions/run.png'),"Run")
        executeBlock = self.MyToolbar.addAction(QIcon(params['path']+params['directories.crystalIcons']+'/actions/kde1.png'),"Run Block")
        executeSelection = self.MyToolbar.addAction(QIcon(params['path']+params['directories.crystalIcons']+'/actions/kde4.png'),"Run Selection")

        self.MyToolbar.addSeparator()

        changeWorkingPath = self.MyToolbar.addAction(workingPathIcon,"Change working path")
        killThread = self.MyToolbar.addAction(killThreadIcon,"Kill Thread")
        
        self.connect(killThread,SIGNAL("triggered()"),self.terminateCodeExecution)

        self.connect(changeWorkingPath, SIGNAL('triggered()'), self.changeWorkingPath)

        self.connect(newFile, SIGNAL('triggered()'), self.Editor.newEditor)
        self.connect(openFile, SIGNAL('triggered()'), self.Editor.openFile)
        self.connect(saveFile, SIGNAL('triggered()'), lambda : self.Editor.Tab.currentWidget().saveFile())
        self.connect(saveFileAs, SIGNAL('triggered()'), lambda : self.Editor.Tab.currentWidget().saveFileAs())
        
        self.setWindowIcon(QIcon(params['path']+params['directories.crystalIcons']+'/apps/penguin.png'))
        
        #We add a timer
        self.queuedText = ""
        
                
        self.errorProxy = LogProxy(self.MyLog.writeStderr)
        self.eventProxy = LogProxy(self.MyLog.writeStdout)

        settings = QSettings()

        if settings.contains('Editor/WorkingPath'):
          self.changeWorkingPath(settings.value('Editor/WorkingPath').toString())

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
