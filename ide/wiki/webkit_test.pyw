import sys

import os
import os.path


import mimetypes
import threading

import random
import time


from PyQt4.QtGui import * 
from PyQt4.QtCore import *
from PyQt4 import QtWebKit

from pyview.config.parameters import *

class MyWebView(QtWebKit.QWebView):

  def execCommand(self,cmd,*args): 
    frame = self.page().mainFrame()
    argstr = ""
    js = None
    if args != None:  
      for a in args:
       argstr+='"%s"' % a+","
      argstr = argstr[:len(argstr)-1]
    if argstr != "":
      js = QString("document.execCommand(\"%1\", false, %2)").arg(cmd).arg(argstr)
    else:
      js = QString("document.execCommand(\"%1\", false, null)").arg(cmd)
    print "Executing \"%s\"" % js
    frame.evaluateJavaScript(js)
  
  def __getattr__(self, name):
    return lambda *args:self.execCommand(name,*args)    
    
  def mouseMoveEvent(self,e):
#    print "x: %f, y: %f" % (e.x(),e.y())
    QtWebKit.QWebView.mouseMoveEvent(self,e)
    frame = self.page().mainFrame()
    result = frame.hitTestContent(e.pos())

class Editor(QMainWindow):

  def __init__(self):
    QMainWindow.__init__(self)
    self.webview = MyWebView()
#    self.webview.setUrl(QUrl("http://www.google.com"))
    self.webview.setHtml(
    """
<HTML contenteditable="true">
<head><Title>Example For contenteditable</Title></head>
<BODY>
<p >contenteditable</p>
<img src="http://matplotlib.sourceforge.net/_images/simple_plot.png">

</BODY>
</HTML> 
    """
    )
    self.setCentralWidget(self.webview)
    self.toolbar = QToolBar()
    self.formatToolbar = QToolBar()
    
    newIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/filenew.png')
    openIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/fileopen.png')
    saveIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/filesave.png')
    saveAsIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/filesaveas.png')
    closeIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/fileclose.png')
    exitIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/exit.png')
    workingPathIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/gohome.png')
    killThreadIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/stop.png')
    
    simpleCommands = [
    {'name': "justifyleft" , 'icon' : "text_align_left.png", 'text': "Justify left"},
    {'name': "justifycenter" , 'icon' : "text_align_center.png", 'text': "Justify center"},
    {'name': "justifyright" , 'icon' : "text_align_right.png", 'text': "Justify right"},
    {'name': "justify" , 'icon' : "text_align_justify.png", 'text': "Justify right"},
    {'name': "insertorderedlist" , 'icon' : "text_list_numbers.png", 'text': "Insert ordered list"},
    {'name': "insertunorderedlist" , 'icon' : "text_list_bullets.png", 'text': "Insert unordered list"},
    {'name': "formatBlock" , 'icon' : "text_heading_1.png", 'text': "Heading 1","params" : ["h1"]},
    {'name': "formatBlock" , 'icon' : "text_heading_2.png", 'text': "Heading 2","params" : ["h2"]},
    {'name': "formatBlock" , 'icon' : "text_heading_3.png", 'text': "Heading 3","params" : ["h3"]},
    {'name': "formatBlock" , 'icon' : "text_kerning.png", 'text': "Preformatted","params" : ["pre"]},
    {'name': "formatBlock" , 'icon' : "house.png", 'text': "Address","params" : ["address"]},
    {'name': "formatBlock" , 'icon' : "text_dropcaps.png", 'text': "Paragraph","params" : ["p"]},
    {'name': "subscript" , 'icon' : "text_subscript.png", 'text': "Subscript"},
    {'name': "superscript" , 'icon' : "text_superscript.png", 'text': "Superscript"},
    {'name': "createlink" , 'icon' : "link.png", 'text': "Link","params" : ["http://www.spiegel.de"]},
    {'name': "insertimage" , 'icon' : "image_add.png", 'text': "Link","params" : ["http://www.maxpower.ca/wp-images/icons/sanscons_screenshot.jpg"]},
    ]
    

    for command in simpleCommands:
      print "Adding %s" % command['name']
      icon = QIcon(params['path']+params['directories.famfamIcons']+command['icon'])
      action = self.formatToolbar.addAction(icon,command['text'])
      try:
        self.connect(action,SIGNAL("triggered()"),lambda x = command['name'],params = command['params']: self.webview.execCommand(x,tuple(params)))
      except KeyError:
        self.connect(action,SIGNAL("triggered()"),lambda x = command['name']: self.webview.execCommand(x))
        
    newFile = self.toolbar.addAction(newIcon,"New")
    openFile = self.toolbar.addAction(openIcon,"Open")
    saveFile = self.toolbar.addAction(saveIcon,"Save")
    saveFileAs = self.toolbar.addAction(saveAsIcon,"Save As")


    self.addToolBar(self.toolbar)
    self.addToolBar(self.formatToolbar)


if __name__ == '__main__':
  app = QApplication(sys.argv)


  MyWindow = Editor()
  MyWindow.show()

  app.exec_()