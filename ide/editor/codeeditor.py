import re
from PyQt4.QtGui import * 
from PyQt4.QtCore import *
from syntaxhighlighter import *
from pyview.config.parameters import *
from pyview.helpers.coderunner import CodeRunner

import traceback
import math
import sys
import time

from pyview.ide.patterns import ObserverWidget

DEVELOPMENT = False

class ErrorConsole(QTreeWidget,ObserverWidget):

  def __init__(self,codeEditorWindow,codeRunner,parent = None):
    self._codeEditorWindow = codeEditorWindow
    self._codeRunner = codeRunner
    QTreeWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self.connect(self,SIGNAL("itemDoubleClicked(QTreeWidgetItem *,int)"),self.itemDoubleClicked)
    self.setColumnCount(2)
    self.setColumnWidth(0,400)
    self.setHeaderLabels(["filename","line"])
    
  def updatedGui(self,subject,property,value = None):
    if subject == self._codeRunner and property == "exceptions":
      for info in value:
        self.processErrorTraceback(info)
      self._codeRunner.clearExceptions()
      
  def itemDoubleClicked(self,item,colum):
    if item.parent() != None:
      filename = unicode(item.text(0))
      line = int(item.text(1))
      editor = self._codeEditorWindow.openFile(filename)
      if editor == None:
        return
      editor.highlightLine(line)
    
  def processErrorTraceback(self,exceptionInfo):

    while self.topLevelItemCount() > 20:
      self.takeTopLevelItem(self.topLevelItemCount()-1)

    (exception_type,exception_value,tb) = exceptionInfo

    text = traceback.format_exception_only(exception_type,exception_value)[0]
  
    text = text.replace("\n"," ")
    
    tracebackEntries = traceback.extract_tb(tb)
    exceptionItem = QTreeWidgetItem()
    
    
    font = QFont()
    font.setPixelSize(14)

    exceptionItem.setFont(0,font)
    
    self.insertTopLevelItem(0,exceptionItem)

    exceptionItem.setText(0,text)
    exceptionItem.setFirstColumnSpanned(True)
    exceptionItem.setFlags(Qt.ItemIsEnabled)
    
    for entry in tracebackEntries[1:]:
      (filename, line_number, function_name, text) = entry
      
      if os.path.exists(filename) and os.path.isfile(filename):
        item = QTreeWidgetItem()
        exceptionItem.addChild(item)
        item.setText(0,filename)
        item.setText(1,str(line_number))
          
class CodeEditorWindow(QWidget):

    def checkForOpenFile(self,filename):
      if filename == None:
        return None
      path = os.path.normpath(filename)
      for i in range(0,self.Tab.count()):
        if self.Tab.widget(i).fileName() == path:
          self.Tab.setCurrentWidget(self.Tab.widget(i))
          return self.Tab.widget(i)
      return None
            
    def openFile(self,filename = None):
      if self.checkForOpenFile(filename) != None:
        return self.checkForOpenFile(filename) 
      MyEditor = CodeEditor(codeRunner = self.codeRunner())
      if MyEditor.openFile(filename) == True:
        self.newEditor(MyEditor)
        MyEditor.updateTab()
        self.saveTabState()
        return MyEditor
      else:
        del MyEditor
      return None
      
    def stopExecution(self):
      self.Tab.currentWidget().stopExecution()

    def executeBlock(self):
        self.Tab.currentWidget().executeBlock()

    def newEditor(self,Editor = None):
        MyEditor = None
        if Editor != None:
          MyEditor = Editor
        else:
          MyEditor = CodeEditor(codeRunner = self.codeRunner())
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
      openFiles = list()
      for i in range(0,self.Tab.count()):
        widget = self.Tab.widget(i)
        if widget.fileName() != None:
          openFiles.append(QString(widget.fileName()))
      settings = QSettings()
      settings.setValue('Editor/OpenFiles',openFiles)
        
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
      
    def codeRunner(self):
      return self._codeRunner
      
    def __init__(self,parent=None,gv = dict(),lv = dict(),codeRunner = CodeRunner()):
        self.editors = []
        self.count = 1
        self._gv = gv
        self._lv = lv
        self._codeRunner = codeRunner
        QWidget.__init__(self,parent)

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
        settings = QSettings()
        if settings.contains("Editor/OpenFiles"):
          openFiles = settings.value("Editor/OpenFiles").toList()
          if openFiles != None:
            for file in openFiles:
              editor = self.newEditor()
              editor.openFile(file.toString())  
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
            width = QFontMetrics(self.edit.document().defaultFont()).width(str(maxline)) + 10+10
            if self.width() != width:
                self.setFixedWidth(width)
                margins = QMargins(width,0,0,0)
                self.edit.setViewportMargins(margins)
                self.edit.viewport().setContentsMargins(margins)
            QWidget.update(self, *args)
            
        def mousePressEvent(self,e):
          print "Mouse pressed!"
          block = self.edit.firstVisibleBlock()
          viewport_offset = self.edit.contentOffset()
          blockFound = False
          changed = False
          while block.isValid():
            
            if not block.isVisible():
              position = self.edit.blockBoundingGeometry(block).topLeft()+viewport_offset
              if abs(e.pos().y()-position.y()) < 10 or blockFound:
                block.setVisible(True)
                changed = True
                blockFound = True
            else:
              blockFound = False
               
            block = block.next()
            if changed:
              self.edit.viewport().update()
  
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
  
                invisibleBlock = False
                
                while not block.isVisible():
                  invisibleBlock = True
                  block = block.next()
  
                # The top left position of the block in the document
                position = self.edit.blockBoundingGeometry(block).topLeft()+viewport_offset
                # Check if the position of the block is out side of the visible
                # area.
                if position.y() > page_bottom:
                    break
                
                line_count = block.firstLineNumber()+1
                
                if invisibleBlock:
                  painter.drawLine(0, round(position.y()),self.edit.width()-self.width(),round(position.y()))
                  continue
    
                # We want the line number for the selected line to be bold.
                bold = False
                if block == current_block:
                    bold = True
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
 
                # Draw the line number right justified at the y position of the
                # line. 3 is a magic padding number. drawText(x, y, text).
                painter.drawText(self.width() - 10 - font_metrics.width(str(line_count)) - 3, round(position.y()) + font_metrics.ascent()+font_metrics.descent()-1, str(line_count))
 
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
        super(LineTextWidget,self).resizeEvent(e)
        
    def setDefaultFont(self,font):
      self.document().setDefaultFont(font)
 
    def eventFilter(self, object, event):
        # Update the line numbers for all events on the text edit and the viewport.
        # This is easier than connecting all necessary singals.
        if object is self.viewport():
            self.number_bar.update()
            return False
        return QPlainTextEdit.eventFilter(object, event)

class SearchableEditor(object):

  def __init__(self):
    self._panel = QWidget(self)
    self._layout = QBoxLayout(QBoxLayout.LeftToRight)
    self._panel.setLayout(self._layout)
    self._searchText = QLineEdit("test")
    self._replaceText = QLineEdit("replace")
    self._forwardButton = QPushButton("Forward")
    self._backwardButton = QPushButton("Backward")
    self._caseSensitive = QCheckBox("Case Sensitive")
    self._useRegex = QCheckBox("Regex")
    
    self._layout.addWidget(self._searchText)
    self._layout.addWidget(self._replaceText)
    self._layout.addWidget(self._forwardButton)
    self._layout.addWidget(self._backwardButton)
    self._layout.addWidget(self._caseSensitive)
    self._layout.addWidget(self._useRegex)
    self._layout.addStretch()
    self._panel.hide()

    self.connect(self._searchText,SIGNAL("enterPressed()"),self.searchText)
    self.connect(self._forwardButton,SIGNAL("clicked()"),self.searchText)
    self.connect(self._backwardButton,SIGNAL("clicked()"),lambda: self.searchText(backward = True))
    
  def resizeEvent(self,e):
    self._panel.setGeometry(0,self.height()-40,self.width(),40)
    self.adjustMargins()

  def searchText(self,backward = False):
    text = self._searchText.text()
    if self._useRegex.isChecked():
      if backward:
        result = self.document().find(QRegExp(text),self.textCursor().selectionStart(),QTextDocument.FindBackward)
      else:
        result = self.document().find(QRegExp(text),self.textCursor().position())
    else:
      if self._caseSensitive.isChecked():
        if backward:
          result = self.document().find(text,self.textCursor().selectionStart(),QTextDocument.FindCaseSensitively | QTextDocument.FindBackward)
        else:
          result = self.document().find(text,self.textCursor().position(),QTextDocument.FindCaseSensitively)
      else:
        if backward:
          result = self.document().find(text,self.textCursor().selectionStart(),QTextDocument.FindBackward)
        else:
          result = self.document().find(text,self.textCursor().position())
    if not result.isNull():
      self.setTextCursor(result)
      self.ensureCursorVisible()
    

  def replaceText(self):
    pass
    
  def showSearchBar(self):
    self._panel.show()
    self._searchText.setFocus()
    self.adjustMargins()
        
  def hideSearchBar(self):
    self._panel.hide()
    self.setFocus()
    self.adjustMargins()
    
  def adjustMargins(self):
    if self._panel.isVisible():
      margins = self.viewport().contentsMargins()
      margins.setBottom(40)
      self.setViewportMargins(margins)
    else:
      margins = self.viewport().contentsMargins()
      margins.setBottom(0)
      self.setViewportMargins(margins)
          
  def keyPressEvent(self,e):
    if (e.key() == Qt.Key_F) and (e.modifiers() & Qt.ControlModifier):
      self.showSearchBar()
    elif (e.key() == Qt.Key_Escape):
      self.hideSearchBar()
    elif (e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return) and self._panel.isVisible():
      e.accept()
      self.searchText()
    else:
      e.ignore()
    
class CodeEditor(LineTextWidget,SearchableEditor):

    def __init__(self,parent = None,codeRunner = CodeRunner(),lineWrap = True):
        LineTextWidget.__init__(self,parent)
        SearchableEditor.__init__(self)
        self._fileName = None
        self.setTabStopWidth(20)
        self._tabWidget = None
        self._windowManager = None
        self._modifiedAt = None
        self._errorSelections = []
        self._reloadWhenChanged = None
        self._codeRunner = codeRunner
        self._codeId = self._codeRunner.getId()
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
        self.setLineWrap(lineWrap)
        executeBlockShortcut = QShortcut(self)
        executeBlockShortcut.setKey(QKeySequence(Qt.SHIFT+Qt.Key_Return))
        self.connect(executeBlockShortcut,SIGNAL("activated()"),self.executeBlock)
        self.setChanged (False)
        self.updateTab()
        
    def resizeEvent(self,e):
      LineTextWidget.resizeEvent(self,e)
      SearchableEditor.resizeEvent(self,e)
      
    def checkForText(self):
     if self.fileOpenThread.textReady == False:
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(1000)
        self.connect(self.timer,SIGNAL("timeout()"),self.checkForText)
        self.timer.start()
        return
     #self.setPlainText(self.fileOpenThread.text)
          
      
    def highlightLine(self,line):
    
      print "Highlighting line no %d" % line

      block = self.document().findBlockByLineNumber(line-1)
  
      selection = QTextEdit.ExtraSelection()
    
      cursor = self.textCursor()
      cursor.setPosition(block.position()+1)
      cursor.movePosition(QTextCursor.StartOfLine,QTextCursor.KeepAnchor) 
      cursor.movePosition(QTextCursor.EndOfLine,QTextCursor.KeepAnchor) 
      selection.cursor = cursor
      format = QTextCharFormat()
      format.setBackground(QBrush(QColor(255,255,0)))
      format.setProperty(QTextFormat.FullWidthSelection, True)
  
      selection.format = format
  
      cursor = self.textCursor()
      cursor.setPosition(block.position())
      
      self.setTextCursor(cursor)
      self.setErrorSelections([selection])
      self.cursorPositionChanged()
      self.ensureCursorVisible()
      
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
      self._modifiedAt = time.time()+10
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
        
    def updateTab(self):
     filename = '[not saved]'
     if self.fileName() != None:
        self._tabToolTip = self.fileName()
        filename = os.path.basename(self.fileName())
     if self._tabWidget != None:
        changed_text = ""
        running_text = ""
        if self._codeRunner.isExecutingCode(self._codeId):
          running_text = "[running]"
        if self._codeRunner.hasFailed(self._codeId):
          running_text = "[failed]"
        if self._Changed == True:
          changed_text = "*"  
        self._tabWidget.setTabText(self._tabWidget.indexOf(self),running_text+changed_text+filename)
        self._tabWidget.setTabToolTip(self._tabWidget.indexOf(self),changed_text+self.tabToolTip())
    
        
    def saveFileAs(self):
      FileName = QFileDialog.getSaveFileName(filter = "Python(*.py *.pyw)")
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
        FileName = QFileDialog.getOpenFileName(filter = "Python(*.py *.pyw)")
      if os.path.isfile(FileName):
          return self._openCode(FileName)
      return False

    def autoIndentCurrentLine(self):
      cursor = self.textCursor()
      
      start = cursor.position()
      
      cursor.movePosition(QTextCursor.StartOfLine,QTextCursor.MoveAnchor)
      cursor.movePosition(QTextCursor.EndOfLine,QTextCursor.KeepAnchor)
      
      text = cursor.selection().toPlainText()
      
      lastLine = QTextCursor(cursor)
      
      lastLine.movePosition(QTextCursor.PreviousBlock,QTextCursor.MoveAnchor)
      lastLine.movePosition(QTextCursor.StartOfLine,QTextCursor.MoveAnchor)
      lastLine.movePosition(QTextCursor.EndOfLine,QTextCursor.KeepAnchor)

      lastLineText = lastLine.selection().toPlainText()
      
      blankLine = QRegExp("^[\t ]*$")
      
      indents = QRegExp(r"^[ \t]*")
      index = indents.indexIn(lastLineText)
      cursor.insertText(lastLineText[:indents.matchedLength()]+text)
      
      cursor.setPosition(start+indents.matchedLength())
      
      self.setTextCursor(cursor)
        
      
    def indentCurrentSelection(self):
      cursor = self.textCursor()

      start = cursor.selectionStart()
      end = cursor.selectionEnd()

      cursor.setPosition(start,QTextCursor.MoveAnchor)
      cursor.movePosition(QTextCursor.StartOfLine,QTextCursor.MoveAnchor)

      start = cursor.selectionStart()

      cursor.setPosition(end,QTextCursor.KeepAnchor)
      cursor.movePosition(QTextCursor.EndOfLine,QTextCursor.KeepAnchor)

      text = cursor.selection().toPlainText()

      text.replace(QRegExp(r"(\n|^)"),"\\1\t")

      cursor.insertText(text)

      cursor.setPosition(start)
      cursor.setPosition(start+len(text),QTextCursor.KeepAnchor)

      self.setTextCursor(cursor)
              
    def unindentCurrentSelection(self):
      cursor = self.textCursor()

      start = cursor.selectionStart()
      end = cursor.selectionEnd()

      cursor.setPosition(start,QTextCursor.MoveAnchor)

      start = cursor.selectionStart()

      cursor.movePosition(QTextCursor.StartOfLine,QTextCursor.MoveAnchor)
      cursor.setPosition(end,QTextCursor.KeepAnchor)
      cursor.movePosition(QTextCursor.EndOfLine,QTextCursor.KeepAnchor)

      text = cursor.selection().toPlainText()
      
      text.replace(QRegExp(r"(\n)[ \t]([^\n]+)"),"\\1\\2")
      text.replace(QRegExp(r"^[ \t]([^\n]+)"),"\\1")
      
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
      if cursor.position() == block.cursor.selectionStart() and block.cursor.selectionStart() != 0:
        cursor.setPosition(block.cursor.selectionStart()-1)

        block = self.getCurrentBlock()
        cursor.setPosition(block.cursor.selectionStart())
      else:
        cursor.setPosition(block.cursor.selectionStart())
      self.setTextCursor(cursor)
      
    def getCurrentBlock(self):

      text = unicode(self.document().toPlainText())
      cursor = self.textCursor().position() 
      
      blockStart = text.rfind("\n##",0,max(0,cursor-1))+1
      blockEnd = text.find("\n##",cursor)-1
      
      if blockStart == -1:
        blockStart = 0
                
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
      
      self._errorSelections = []

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

    def stopExecution(self):
      if self._codeRunner.isExecutingCode(self._codeId):
        self._codeRunner.stopExecution(self._codeId)
    
    def executeCode(self,code,callback = None):
      if self._codeRunner.isExecutingCode(self._codeId):
        print "Terminate or wait for other thread first..."
        return
      source = "[undefined]"
      if self.fileName() != None:
        source = self.fileName()
      self._codeRunner.executeCode(code,self._codeId,filename = source)
      self.checkRunStatus()
      
    def executeAll(self,callback = None):
        text = self.document().toPlainText()
        self.executeCode(text,callback)
    
    def executeSelection(self,callback = None):
        text = self.textCursor().selection().toPlainText()
        self.executeCode(unicode(text),callback)
        
    def executeString(self,string,callback = None):
      self.executeCode(unicode(string),callback)

    def executeBlock(self,callback = None):
        selection = self.getCurrentBlock()
        block = self.document().findBlock(selection.cursor.selectionStart())
        n = block.firstLineNumber()
        self.executeCode("\n"*n+unicode(selection.cursor.selection().toPlainText())+u"\n",callback)

    def hideBlock(self):
      print "Hiding..."
      block = QTextBlock()
      selection = self.textCursor().block()
      selection.setVisible(False)
      self.viewport().update()

    def contextMenuEvent(self,event):
        MyMenu = self.createStandardContextMenu()
        if self.thread != None and self._codeRunner.isExecutingCode(self._codeId):
          stopExecution = MyMenu.addAction("terminate execution")
          self.connect(stopExecution, SIGNAL('triggered()'), self.stopExecution)
        else:
          MyMenu.addSeparator()
          executeBlock = MyMenu.addAction("execute block")
          executeSelection = MyMenu.addAction("execute selection")
          executeAll = MyMenu.addAction("execute all")
          executeBlock.setShortcut(QKeySequence(Qt.CTRL+Qt.Key_Return))
          hideBlock = MyMenu.addAction("Hide block")
          MyMenu.addSeparator()
          if self._lineWrap:
            lineWrap = MyMenu.addAction("Disable line wrap")
          else:
            lineWrap = MyMenu.addAction("Enable line wrap")
          self.connect(lineWrap,SIGNAL("triggered()"),self.toggleLineWrap)
          self.connect(hideBlock,SIGNAL('triggered()'),self.hideBlock)
          self.connect(executeBlock, SIGNAL('triggered()'), self.executeBlock)
          self.connect(executeSelection, SIGNAL('triggered()'), self.executeSelection)
          self.connect(executeAll, SIGNAL('triggered()'), self.executeAll)
        MyMenu.exec_(self.cursor().pos())
        
    def toggleLineWrap(self):
      self.setLineWrap(not self._lineWrap)
    
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
    
    def checkRunStatus(self,caller = None):
      self.updateTab()
    
    def onTimer(self):
      self.checkForFileModifications()
      self.checkRunStatus()
      
    def activateBlockHighlighting(self,activate = False):
      self._blockHighlighting = activate
    
    def updateUndoStatus(self,status):
      self.setChanged(status)
        
    def keyPressEvent(self,e):
      SearchableEditor.keyPressEvent(self,e)
      if e.isAccepted():
        return
      if (e.key() == Qt.Key_Enter):
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
      if e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter:
        self.autoIndentCurrentLine()
        
      
    def setWindowManager(self,manager):
      self._windowManager = manager
      
    def windowManager(self):
      return self._windowManager
      
    def setLineWrap(self,state):
      self._lineWrap = state
      if state:
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
      else:
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
