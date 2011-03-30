#!/usr/bin/env python
# -*- coding: latin1 -*-

"""
Basic use of the QScintilla2 widget

Note : name this file "qt4_sci_test.py"
"""

import sys
from PyQt4.QtGui import QApplication
from PyQt4 import QtCore, QtGui
from PyQt4.Qsci import QsciScintilla, QsciScintillaBase, QsciLexerPython

class MyScintilla(QsciScintilla):
  
  def __init__(self):
    QsciScintilla.__init__(self)
    
  def keyPressEvent(self,e):
    print "Key pressed!"
    QsciScintilla.keyPressEvent(self,e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = MyScintilla()

    ## define the font to use
    font = QtGui.QFont()
    font.setFamily("Consolas")
    font.setFixedPitch(True)
    font.setPointSize(10)
    # the font metrics here will help
    # building the margin width later
    fm = QtGui.QFontMetrics(font)

    ## set the default font of the editor
    ## and take the same font for line numbers
    editor.setFont(font)
    editor.setMarginsFont(font)

    ## Line numbers
    # conventionnaly, margin 0 is for line numbers
    editor.setMarginWidth(0, fm.width( "00000" ) + 5)
    editor.setMarginLineNumbers(0, True)

    ## Edge Mode shows a red vetical bar at 80 chars
    editor.setEdgeMode(QsciScintilla.EdgeLine)
    editor.setEdgeColumn(80)
    editor.setEdgeColor(QtGui.QColor("#FF0000"))

    ## Folding visual : we will use boxes
    editor.setFolding(QsciScintilla.BoxedTreeFoldStyle)

    ## Braces matching
    editor.setBraceMatching(QsciScintilla.SloppyBraceMatch)

    ## Editing line color
    editor.setCaretLineVisible(True)
    editor.setCaretLineBackgroundColor(QtGui.QColor("#CDA869"))

    ## Margins colors
    # line numbers margin
    editor.setMarginsBackgroundColor(QtGui.QColor("#333333"))
    editor.setMarginsForegroundColor(QtGui.QColor("#CCCCCC"))

    # folding margin colors (foreground,background)
    editor.setFoldMarginColors(QtGui.QColor("#99CC66"),QtGui.QColor("#333300"))

    ## Choose a lexer
    lexer = QsciLexerPython()
    lexer.setDefaultFont(font)
    editor.setLexer(lexer)

    ## Render on screen
    editor.show()

    ## Show this file in the editor
    editor.setText(open("scintilla_test.py").read())
    sys.exit(app.exec_())
