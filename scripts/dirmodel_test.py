import sys
import getopt

sys.path.append('.')
sys.path.append('../')

from PySide.QtGui import * 
from PySide.QtCore import *

cnt = 0
ID=0


import os
import os.path
import time

class SmartTreeView(QTreeView):

  def __init__(self,parent = None):
    QTreeView.__init__(self,parent)
    

app = QApplication(sys.argv)

MyWindow = QWidget()

MyTreeView = SmartTreeView()

MyModel = QFileSystemModel()
MyModel.setRootPath("c:\\")
MyModel.setReadOnly(False)
MyModel.setFilter(QDir.AllDirs)

MyTreeView.setModel(MyModel)

MyLayout = QGridLayout()

MyLayout.addWidget(MyTreeView,0,0)

MyWindow.setLayout(MyLayout)

MyWindow.show()

app.exec_()



    