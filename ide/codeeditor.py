import re
from PySide.QtGui import * 
from PySide.QtCore import *
from syntaxhighlighter import *
from preferences import *
from pyview.conf.parameters import *

import traceback
import math
import sys
import time

from pyview.lib.patterns import KillableThread,StopThread,ReloadableWidget

DEVELOPMENT = False

class CodeThread (KillableThread,QThread):

  def __init__(self,code,gv = globalVariables,lv = globalVariables,callback = None,source = "<my string>"):
    KillableThread.__init__(self)
    QThread.__init__(self)
    self._gv = gv
    self._lv = lv
    self._source = source
    self._failed = False
    self._callback = callback
    self.code = code
    
  def isRunning(self):
    return self.isAlive()
    
  def failed(self):
    return self._failed
    
  def run(self):
    try:
      code = compile(self.code,self._source,'exec')
      exec(code,self._gv,self._gv)
    except StopThread:
      print "Thread termination requested, exiting..."
    except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      self._exception_type = exc_type
      self._exception_value = exc_value
      self._traceback = exc_traceback
      self._failed = True
      raise
    finally:
      if not self._callback == None:
        self._callback(self)
    
    

class CodeEditorWindow(QWidget,ReloadableWidget):

    def checkForOpenFile(self,filename):
      if filename == None:
        return None
      path = os.path.normpath(filename)
      for i in range(0,self.Tab.count()):
        if self.Tab.widget(i).fileName() == path:
          self.Tab.setCurrentWidget(self.Tab.widget(i))
          return self.Tab.widget(i)
      return None
      
    def processErrorTraceback(self,tb,exception_type,exception_value):

      text = traceback.format_exception_only(exception_type,exception_value)[0]
    
      tracebackEntries = traceback.extract_tb(tb)
      
      if self.errorConsole() == None:
        return
      
      console = self.errorConsole()

      self.connect(console,SIGNAL("anchorClicked(const QUrl&)"),self.showErrorLink)
      
      console.setOpenLinks(False)

      html = "<h1>Errors</h1><p>%s</p><h2>Traceback</h2><ul>" % text
      
      for entry in tracebackEntries[1:]:
        (filename, line_number, function_name, text) = entry
        
        html+="<li><a href=\"file:%s::%d\">%s, line %d</a></li>" % (filename,line_number,filename,line_number)
        
      html+= "</ul>"
    
      console.setHtml(html)
      
    def openFile(self,filename = None):
      if self.checkForOpenFile(filename) != None:
        return self.checkForOpenFile(filename) 
      MyEditor = CodeEditor()
      if MyEditor.openFile(filename) == True:
        self.newEditor(MyEditor)
        MyEditor.updateTab()
        self.saveTabState()
        return MyEditor
      else:
        del MyEditor
      return None
      
    def killThread(self):
      self.Tab.currentWidget().killThread()

    def executeCode(self):
        self.Tab.currentWidget().executeBlock()

    def newEditor(self,Editor = None):
        MyEditor = None
        if Editor != None:
          MyEditor = Editor
        else:
          MyEditor = CodeEditor()
          MyEditor.append("")
        MyEditor.setTabWidget(self.Tab)
        MyEditor.activateHighlighter()
        self.editors.append(MyEditor)
        self.Tab.addTab(MyEditor,"untitled %i" % self.count)
        self.Tab.setTabToolTip(self.Tab.indexOf(MyEditor),"untitled %i" % self.count)
        self.count = self.count + 1
        self.Tab.setCurrentWidget(MyEditor)
        MyEditor.setWindowManager(self)
        return MyEditor

    def addEditor(self):
        self.newEditor()
        
    def saveTabState(self):
      MyPrefs = Preferences()
      openFiles = list()
      for i in range(0,self.Tab.count()):
        widget = self.Tab.widget(i)
        if widget.fileName() != None:
          print widget.fileName()
          openFiles.append(widget.fileName())
      MyPrefs.set('openFiles',openFiles)
      MyPrefs.save()
        
    def closeEvent(self,e):
      self.saveTabState()
      for i in range(0,self.Tab.count()):
        widget = self.Tab.widget(i)
        widget.closeEvent(e)
        
    def closeTab(self,index):
      window = self.Tab.widget(index)
      if window.close():
        window.destroy()
        self.Tab.removeTab(index)
        if self.Tab.count() == 0:
          self.newEditor()
        self.saveTabState()
          
    def executeCode(self,index = None):
      code = self.commandInput.currentText()
      self.Tab.currentWidget().executeString(code)
      if self.commandInput.findText(self.commandInput.currentText(),Qt.MatchExactly) == -1 :
        self.commandInput.insertItem(0,self.commandInput.currentText())

    def showErrorLink(self,url):
      (filename,line) = str(url.path()).split("::")
      line = int(line)
      self.errorConsole().setSource(self.errorConsole().source())

      widget = self.openFile(filename)

      if widget != None:

        block = widget.document().findBlockByLineNumber(line-1)
  
        selection = QTextEdit.ExtraSelection()
      
        cursor = widget.textCursor()
        cursor.setPosition(block.position())
        cursor.movePosition(QTextCursor.EndOfLine,QTextCursor.KeepAnchor) 
        selection.cursor = cursor
        format = QTextCharFormat()
        format.setBackground(QBrush(QColor(255,255,0)))
        format.setProperty(QTextFormat.FullWidthSelection, True)

        selection.format = format

        cursor = widget.textCursor()
        cursor.setPosition(block.position())
        
        widget.setTextCursor(cursor)
    
        widget.setErrorSelections([selection])

        widget.cursorPositionChanged()
      
        widget.ensureCursorVisible()
      
    def setErrorConsole(self,console):
      self.connect(console,SIGNAL("anchorClicked(const QUrl & link"),self.showErrorLink)
      self._errorConsole = console
      
    def errorConsole(self):
      return self._errorConsole

    def __init__(self,parent=None):
        self.editors = []
        self.count = 1
        self._errorConsole = None
        QWidget.__init__(self,parent)
        ReloadableWidget.__init__(self)

        MyLayout = QGridLayout()
        
        self.Tab = QTabWidget()
        
        commandLayout = QBoxLayout(QBoxLayout.LeftToRight)
                
        self.commandInput = self.MyComboBox()
        self.commandInput.setEditable(True)
        self.executeCommand = QPushButton("Execute")

        self.executeCommand.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Preferred)

        commandLayout.addWidget(self.commandInput)
        commandLayout.addWidget(self.executeCommand)
        
        self.connect(self.commandInput,SIGNAL("returnPressed()"),self.executeCode)
        self.connect(self.executeCommand,SIGNAL("clicked()"),self.executeCode)

        self.Tab.setTabsClosable(True)
        self.connect(self.Tab,SIGNAL("tabCloseRequested(int)"),self.closeTab)

        MyPrefs = Preferences()
        openFiles = MyPrefs.get('openFiles')
        if openFiles != None:
          for file in openFiles:
            editor = self.newEditor()
            editor.openFile(file)  
        else:
          self.newEditor()
        MyLayout.addWidget(self.Tab,0,0)
        MyLayout.addLayout(commandLayout,1,0)

        self.setLayout(MyLayout)

##Subclasses for internal use only...
    
    class MyComboBox(QComboBox):
      
      def keyPressEvent(self,e):
        QComboBox.keyPressEvent(self,e)
        if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
          self.emit(SIGNAL("returnPressed()"))



class LineNumbers(QTextEdit):

  def __init__(self,parent,width = 50):
    QTextEdit.__init__(self,parent)
    self.setFixedWidth(width)
    self.setReadOnly(True)
    MyDocument = self.document() 
    MyDocument.setDefaultFont(parent.document().defaultFont())
    self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.setDisabled(True)

class LineTextWidget(QPlainTextEdit):
 
    def append(self,string):
        self.appendPlainText(string)
 
    class NumberBar(QWidget): 
    
        def __init__(self, *args):
            QWidget.__init__(self, *args)
            self.edit = None
            # This is used to update the width of the control.
            # It is the highest line that is currently visibile.
            self.highest_line = 0
 
        def setTextEdit(self, edit):
            self.edit = edit
 
        def update(self, *args):
            maxline = self.edit.document().lastBlock().firstLineNumber()+self.edit.document().lastBlock().lineCount()
            width = QFontMetrics(self.edit.document().defaultFont()).width(str(maxline)) + 10
            if self.width() != width:
                self.setFixedWidth(width)
                self.edit.setViewportMargins(width,0,0,0)
            QWidget.update(self, *args)
 
        def paintEvent(self, event):
            contents_y = 0
            page_bottom = self.edit.viewport().height()
            font_metrics = QFontMetrics(self.edit.document().defaultFont())
            current_block = self.edit.document().findBlock(self.edit.textCursor().position())
 
            painter = QPainter(self)
 
            # Iterate over all text blocks in the document.
            block = self.edit.firstVisibleBlock()
            viewport_offset = self.edit.contentOffset()
            line_count = block.blockNumber()
            painter.setFont(self.edit.document().defaultFont())
            while block.isValid():
                line_count += 1
 
                # The top left position of the block in the document
                position = self.edit.blockBoundingGeometry(block).topLeft()+viewport_offset
                # Check if the position of the block is out side of the visible
                # area.
                if position.y() > page_bottom:
                    break
 
                # We want the line number for the selected line to be bold.
                bold = False
                if block == current_block:
                    bold = True
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
 
                # Draw the line number right justified at the y position of the
                # line. 3 is a magic padding number. drawText(x, y, text).
                painter.drawText(self.width() - font_metrics.width(str(line_count)) - 3, round(position.y()) + font_metrics.ascent()+font_metrics.descent()-1, str(line_count))
 
                # Remove the bold style if it was set previously.
                if bold:
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)
 
                block = block.next()
 
            self.highest_line = line_count
            painter.end()
 
            QWidget.paintEvent(self, event)
 
 
    def __init__(self, *args):
        QPlainTextEdit.__init__(self, *args)
  
        self.number_bar = self.NumberBar(self)
        self.number_bar.setTextEdit(self)
 
        self.viewport().installEventFilter(self)

    def resizeEvent(self,e):
        self.number_bar.setFixedHeight(self.height())
        QPlainTextEdit.resizeEvent(self,e)
        
    def setDefaultFont(self,font):
      self.document().setDefaultFont(font)
 
    def eventFilter(self, object, event):
        # Update the line numbers for all events on the text edit and the viewport.
        # This is easier than connecting all necessary singals.
        if object is self.viewport():
            self.number_bar.update()
            return False
        return QPlainTextEdit.eventFilter(object, event)

    
class CodeEditor(LineTextWidget):


    def checkForText(self):
     if self.fileOpenThread.textReady == False:
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(1000)
        self.connect(self.timer,SIGNAL("timeout()"),self.checkForText)
        self.timer.start()
        return
     #self.setPlainText(self.fileOpenThread.text)
          
      
    def setTabWidget(self,widget):
      self._tabWidget = widget
      
    def fileName(self):
      return self._fileName
      
    def _setFileName(self,filename):
      self._fileName = os.path.normpath(str(filename))
      if re.search(".py$",self._fileName) or re.search(".pyw$",self._fileName):
        self.activateHighlighter(True)
      else:
        self.activateHighlighter(False)
      if os.path.exists(self.fileName()):
        self._modifiedAt = os.path.getmtime(self._fileName)
      else:
        self._modifiedAt = 0

    def activateHighlighter(self,activate = True):
      if activate:
        self.highlighter = Python( self.document() )
      else:
        if hasattr(self,"highlighter"):
          del self.highlighter
  
    def _saveCode(self):
      if self.fileName() == None:
        return
      self._modifiedAt = time.time()
      try:
        file = open(self.fileName(),'w')
        file.write(unicode(self.document().toPlainText()))
        file.close()
        self.setChanged(False)
        self._modifiedAt = os.path.getmtime(self.fileName())+10
      finally:
        file.close()
            
    def _openCode(self,filename):
      if os.path.isfile(filename):
        try:
          file = open(filename,'r')
          text = file.read()   
        except IOError:
          print "Could not read file!"
          return False
        self.setPlainText(text)
        self._setFileName(filename)
        self.updateTab()
        self.setChanged(False)
        return True
      return False
            
    def setChanged(self,hasChanged = True):
      self._Changed = hasChanged
      self.document().setModified(hasChanged)
      self.updateTab()
        

    def saveFile(self):
      if self.fileName() == None:
        return self.saveFileAs()
      else:
        self._saveCode()
        return True
        
    def updateTab(self,failedThread = False):
     if self._tabWidget != None:
        changed_text = ""
        thread_text = ""
        if self._Changed == True:
          changed_text = "*"  
        if failedThread:
          changed_text+="!"
        if self._threadStatus == True:
          thread_text = "[running...]"
        filename = '[not saved]'
        if self.fileName() != None:
          self._tabToolTip = self.fileName()
          filename = os.path.basename(self.fileName())
        self._tabWidget.setTabText(self._tabWidget.indexOf(self),changed_text+filename+thread_text)
        self._tabWidget.setTabToolTip(self._tabWidget.indexOf(self),changed_text+self.tabToolTip()+thread_text)
    
        
    def saveFileAs(self):
      FileName = QFileDialog.getSaveFileName()[0]
      if FileName != '':
        print "Saving document as %s" % FileName
        if os.path.isfile(FileName):
          pass
        self._setFileName(FileName)
        self._saveCode()
        self.updateTab()
        return True
      else:
        return False
      
    def openFile(self,FileName = None):
      if FileName == None:
        FileName = QFileDialog.getOpenFileName()[0]
      if os.path.isfile(FileName):
          return self._openCode(FileName)
      return False
      
    def indentCurrentSelection(self):
      text = self.textCursor().selection().toPlainText()
      cursor = self.textCursor()
      currentPos = cursor.position()
      start = cursor.selectionStart()
      text.replace(QRegExp(r"(\n|^)"),"\\1\t")
      cursor.insertText(text)
      cursor.setPosition(start)
      cursor.setPosition(start+len(text),QTextCursor.KeepAnchor)
      self.setTextCursor(cursor)
              
    def unindentCurrentSelection(self):
      cursor = self.textCursor()
      newCursor = self.textCursor()
      newCursor.setPosition(cursor.selectionStart())
      newCursor.setPosition(cursor.selectionEnd(),QTextCursor.KeepAnchor)
      text = newCursor.selection().toPlainText()
      currentPos = cursor.position()
      start = cursor.selectionStart()
      text.replace(QRegExp(r"(\n)\s"),"\\1")
      text.replace(QRegExp(r"^(\s*)\s"),"\\1")
      cursor.insertText(text)
      cursor.setPosition(start)
      cursor.setPosition(start+len(text),QTextCursor.KeepAnchor)
      self.setTextCursor(cursor)
              

    def gotoNextBlock(self):
      block = self.getCurrentBlock()
      cursor = self.textCursor()
      cursor.setPosition(block.cursor.selectionEnd())
      if not cursor.atEnd():
        cursor.setPosition(block.cursor.selectionEnd()+1)
      self.setTextCursor(cursor)
      
    def gotoPreviousBlock(self):
      block = self.getCurrentBlock()
      cursor = self.textCursor()
      if cursor.position() == block.cursor.selectionStart():
        cursor.setPosition(block.cursor.selectionStart())
        if not cursor.atStart():
          cursor.setPosition(block.cursor.selectionStart()-1)
        
        self.setTextCursor(cursor)
        block = self.getCurrentBlock()
        cursor.setPosition(block.cursor.selectionStart())
      else:
        cursor.setPosition(block.cursor.selectionStart())
      self.setTextCursor(cursor)
      
    def getCurrentBlock(self):

      text = self.document().toPlainText()
      cursor = self.textCursor().position() 
      
      blockStart = text.rfind("\n##",0,max(0,cursor-1))
      blockEnd = text.find("\n##",cursor)
      
      if blockStart == -1:
        blockStart = 0
      else:
        blockStart+= text.find("\n",blockStart)-blockStart
                
      if blockStart == blockEnd:
        return None
        
      if blockEnd != -1:
        blockEnd+=1

      selection = QTextEdit.ExtraSelection()
      
      cursor = self.textCursor()

      cursor.setPosition(blockStart,QTextCursor.MoveAnchor)
      
      if blockEnd != -1:
        cursor.setPosition(blockEnd,QTextCursor.KeepAnchor)
      else:
        cursor.movePosition(QTextCursor.End,QTextCursor.KeepAnchor)

      selection.cursor = cursor

      return selection
  
    def cursorPositionChanged(self):
      if self._blockHighlighting == False:
        return
        
      selection = self.getCurrentBlock()

      if selection == None:
        return

      selections = []
      
      selections.extend(self._errorSelections)

      selection = self.getCurrentBlock()
      
      selection.format = QTextCharFormat()
      pen = QPen()
#      selection.format.setProperty(QTextFormat.OutlinePen,pen)
#      selection.format.setBackground(QBrush(QColor(240,240,240)))
#      selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            
      selections.append(selection)    
      
      self.setExtraSelections(selections)

      
    def setErrorSelections(self,selections):
      self._errorSelections = selections
      
    def errorSelections(self):
      return self._errorSelections
      
    def tabToolTip(self):
      return self._tabToolTip
              
    def requestClose(self):
      if self._Changed:
        MyMessageBox = QMessageBox()
        MyMessageBox.setWindowTitle("Warning!")
        MyMessageBox.setText("Save changes made to file \"%s\"?" % self.tabToolTip())
        yes = MyMessageBox.addButton("Yes",QMessageBox.YesRole)
        no = MyMessageBox.addButton("No",QMessageBox.NoRole)
        cancel = MyMessageBox.addButton("Cancel",QMessageBox.RejectRole)
        MyMessageBox.exec_()
        choice = MyMessageBox.clickedButton()
        if choice == yes:
          return self.saveFile()
        elif choice == no:
          return True
        return False
      
    def closeEvent(self,e):
      if self.requestClose() == False:
        e.ignore()

    def killThread(self):
      if self.thread == None:
        return
      self.thread.terminate()
      self._killThread = True
      self._killTime = time.time()
    
    def _execCode(self,code,callback = None):
      if self.thread != None:
        if self.thread.isRunning():
          print "Terminate or wait for other thread first..."
          return
        else:
          self.thread = None
      self._killThread = False
      self._variables["globals"] = self._globalVariables
      source = "[undefined]"
      if self.fileName() != None:
        source = self.fileName()
      self.thread = CodeThread(code,self._variables,self._variables,callback,source = source)
      self.thread.setDaemon(True)
      self.thread.start()
      self.checkThreadStatus()
      
    def executeAll(self,callback = None):
        text = self.document().toPlainText()
        self._execCode(text,callback)
    
    def executeSelection(self,callback = None):
        text = self.textCursor().selection().toPlainText()
        self._execCode(unicode(text),callback)
        
    def executeString(self,string,callback = None):
      self._execCode(unicode(string),callback)

    def executeBlock(self,callback = None):
        selection = self.getCurrentBlock()
        block = self.document().findBlock(selection.cursor.selectionStart())
        n = block.firstLineNumber()
        self._execCode("\n"*n+unicode(selection.cursor.selection().toPlainText())+u"\n",callback)

    def hideBlock(self):
      print "Hiding..."
      selection = self.getCurrentBlock()
      selection.cursor.block().setVisible(False)

    def contextMenuEvent(self,event):
        MyMenu = self.createStandardContextMenu()
        if self.thread != None and self.thread.isRunning():
          killThread = MyMenu.addAction("terminate execution")
          self.connect(killThread, SIGNAL('triggered()'), self.killThread)
        else:
          executeBlock = MyMenu.addAction("execute block")
          executeSelection = MyMenu.addAction("execute selection")
          executeAll = MyMenu.addAction("execute all")
          executeBlock.setShortcut(QKeySequence(Qt.CTRL+Qt.Key_Return))
          hideBlock = MyMenu.addAction("Hide block")
          self.connect(hideBlock,SIGNAL('triggered()'),self.hideBlock)
          self.connect(executeBlock, SIGNAL('triggered()'), self.executeBlock)
          self.connect(executeSelection, SIGNAL('triggered()'), self.executeSelection)
          self.connect(executeAll, SIGNAL('triggered()'), self.executeAll)
        MyMenu.exec_(self.cursor().pos())
    
    def alertFileContentsChanged(self):
        MyMessageBox = QMessageBox()
        MyMessageBox.setWindowTitle("Warning!")
        MyMessageBox.setText("File contents of \"%s\" have changed. Reload?" % self.tabToolTip())
        yes = MyMessageBox.addButton("Yes",QMessageBox.YesRole)
        no = MyMessageBox.addButton("No",QMessageBox.NoRole)
        never = MyMessageBox.addButton("Never",QMessageBox.RejectRole)
        always = MyMessageBox.addButton("Always",QMessageBox.AcceptRole)
        MyMessageBox.exec_()
        choice = MyMessageBox.clickedButton()
        if choice == yes:
          self.openFile(self.fileName())
        elif choice == no:
          self._modifiedAt = os.path.getmtime(self.fileName())
        elif choice == never:
          self._reloadWhenChanged = False
          self._modifiedAt = os.path.getmtime(self.fileName())
        elif choice == always:
          self._reloadWhenChanged = True
          self.openFile(self.fileName())          
      
    
    def checkForFileModifications(self):
      if self.fileName() != None:
        if os.path.exists(self.fileName()) == False:
          pass
          #File has been deleted...
        else:
          if os.path.getmtime(self.fileName()) > self._modifiedAt:
            if self._reloadWhenChanged == True:
              self.openFile(self.fileName())
            elif self._reloadWhenChanged == False:
              return
            else:
              self.alertFileContentsChanged()
    
    def checkThreadStatus(self,caller = None):
      if self.thread == None:
        if self._threadStatus != False:
          self._threadStatus = False
          self.updateTab()
      else:
        if self.thread.isRunning():
          self._errorSelections = []
          self.cursorPositionChanged()
          if self._threadStatus == False:
            self._threadStatus = True
            self.updateTab()
        else:
          if self._threadStatus == True:
            self._threadStatus = False
          if self.thread.failed():
            if self.windowManager() != None:
              self.windowManager().processErrorTraceback(self.thread._traceback,self.thread._exception_type,self.thread._exception_value)
            self.updateTab(failedThread = True)
          else:
            self.updateTab(failedThread = False)
          self.thread = None
      
    
    def onTimer(self):
      self.checkForFileModifications()
      self.checkThreadStatus()
      if self._killThread and self.thread != None:
        if self.thread.isRunning():
          self.thread.join(0.001)
          if time.time()-self._killTime > 10.0:
            print "Thread hangs, please try to kill again..."
            self._killThread = False
        else:
          self._killThread = False
          self.thread = None
      
    def activateBlockHighlighting(self,activate = False):
      self._blockHighlighting = activate
    
    def updateUndoStatus(self,status):
      self.setChanged(status)
        
    def keyPressEvent(self,e):
      if (e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return) and (e.modifiers() & Qt.ControlModifier):
        self.executeBlock()
        e.accept()
        return
      if (e.key() == Qt.Key_Up or e.key() == Qt.Key_Down) and e.modifiers() & Qt.ControlModifier:
        if e.key() == Qt.Key_Up:
          self.gotoPreviousBlock()
        else:
          self.gotoNextBlock()
        e.accept()
        return
      if (e.key() == Qt.Key_Left or e.key() == Qt.Key_Right) and e.modifiers() & Qt.ControlModifier:
        if e.key() == Qt.Key_Left:
          self.unindentCurrentSelection()
        else:
          self.indentCurrentSelection()
        e.accept()
        return
      LineTextWidget.keyPressEvent(self,e)
      
    def setWindowManager(self,manager):
      self._windowManager = manager
      
    def windowManager(self):
      return self._windowManager
      
    def __init__(self,parent = None):
        LineTextWidget.__init__(self,parent)
        self._fileName = None
        self.thread = None
        self.setTabStopWidth(20)
        self._threadStatus = False
        self._tabWidget = None
        self._windowManager = None
        self._modifiedAt = None
        self._errorSelections = []
        self._reloadWhenChanged = None
        self._killThread = False
        self._killTime = 0
        self._variables = globalVariables
        self._globalVariables = globalVariables
        self._blockHighlighting = True
        self._tabToolTip = '[untitled]'
        self._MyTimer = QTimer(self)
        self.connect(self._MyTimer,SIGNAL("timeout()"),self.onTimer)
        self._MyTimer.start(500)
        self.setAttribute(Qt.WA_DeleteOnClose,True)
        MyFont = QFont("Courier",10)
        self.setDefaultFont(MyFont)
        self.connect(self.document(), SIGNAL('modificationChanged(bool)'), self.updateUndoStatus)
        self.connect(self, SIGNAL("cursorPositionChanged()"),self.cursorPositionChanged)
        #self.setLineWrapMode(QTextEdit.NoWrap)
#        self.setLineWrapColumnOrWidth(160)
        executeBlockShortcut = QShortcut(self)
        executeBlockShortcut.setKey(QKeySequence(Qt.SHIFT+Qt.Key_Return))
        self.connect(executeBlockShortcut,SIGNAL("activated()"),self.executeBlock)
        self.setChanged (False)
        self.updateTab()
