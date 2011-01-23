import sys
import getopt

import pyview.helpers.instrumentsmanager
import pyview.helpers.datamanager as dm


from pyview.lib.datacube import *
from pyview.lib.classes import *
from pyview.lib.patterns import *
from pyview.ide.datacubeview import *
reload(sys.modules['pyview.ide.datacubeview'])
from pyview.ide.datacubeview import *

import numpy
import PyQt4.uic as uic


#from pyview.lib.canvas import *
#reload(sys.modules['pyview.lib.canvas'])
from pyview.lib.canvas import *

import weakref
import gc

import time


class Datacube2DPlot:
  
  def __init__(self):
    pass
    
class Plot3DWidget(QWidget,ObserverWidget):
  pass

class Plot2DWidget(QWidget,ObserverWidget):
  
  def nameSelector(self):
    box = QComboBox()
    names = self._cube.names()
    return box
    
  def updatePlot(self,clear = False):
    if len(self._plots) == 0:
      self.canvas.figure.clf()
      self.canvas.axes = self.canvas.figure.add_subplot(111)
      self.canvas.draw()
      return
    for plot in self._plots:
      plot.lines.set_xdata(plot.cube.column(plot.xname))
      plot.lines.set_ydata(plot.cube.column(plot.yname))
      #This is a bug in matplotlib. We have to call "recache" to make sure that the plot is correctly updated.
      plot.lines.recache()
    if self.canvas.axes.get_autoscale_on() == True:
      self.canvas.axes.relim()
      self.canvas.axes.autoscale_view()
    self.canvas.draw()
    
  def addPlot(self):
    if self._cube == None:
      return
    plot = Datacube2DPlot()
    plot.cube = self._cube 
    plot.xname = str(self.xNames.currentText())
    plot.yname = str(self.yNames.currentText())
    plot.legend = "%s, %s vs. %s" % (self._cube.name(),plot.xname,plot.yname)
    plot.style = 'line'
    plot.lines, = self.canvas.axes.plot(plot.cube.column(plot.xname),plot.cube.column(plot.yname))
    plot.cube.attach(self)
    if not plot.xname in self.xnames:
      self.xnames.append(plot.xname)
    if not plot.yname in self.ynames:
      self.ynames.append(plot.yname)
    if not plot.cube.name() in self.cubes:
      self.cubes.append(str(plot.cube.name()))
    self.legends.append(plot.legend)
    self._plots.append(plot)
    self.canvas.axes.set_xlabel(", ".join(self.xnames))
    self.canvas.axes.set_ylabel(", ".join(self.ynames))
    self.canvas.axes.set_title(", ".join(self.cubes))
    
    plotItem = QTreeWidgetItem([self._cube.name(),plot.xname,plot.yname,"line"])
    self.plotList.addTopLevelItem(plotItem)
    plot.item=plotItem
    self.updatePlot()
    
  def clearPlots(self):
    for plot in self._plots:
      if plot.cube != self._cube:
        plot.cube.detach(self)
    self._plots = []
    self.xnames = []
    self.ynames = []
    self.cubes = []
    self._currentIndex = None
    self.plotList.clear()
    self.legends = []
    self.updatePlot()
    
  def setDatacube(self,cube):
    if self._cube != None:
      found = False
      for plot in self._plots:
        if self._cube == plot.cube:
          found = True
      if found == False:
        self._cube.detach(self)
    self._cube = cube
    cube.attach(self)
    self.updateNames(cube.names())
      
  def updateNames(self,names):
    self.xNames.clear()
    self.yNames.clear()
    for name in sorted(names):
      self.xNames.addItem(name,name)    
      self.yNames.addItem(name,name)
      
  def updatedGui(self,subject = None,property = None,value = None):
    if property == "commit":
      self._updated = False
    if property == "names":
      if subject == self._cube:
        self.updateNames(value)
      
  def onTimer(self):
    if self._updated == True:
      return
    self._updated = True
    self.updatePlot()

  def __init__(self,parent = None):
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self._cube = None
    self._plots = []
    self._updated = False
    self.xnames = []
    self._currentIndex = None
    self.ynames = []
    self.legends = []
    self.cubes = []
    splitter = QSplitter(Qt.Vertical)
    layout = QGridLayout()
    self.timer = QTimer(self)
    self.timer.setInterval(1000)
    self.connect(self.timer,SIGNAL("timeout()"),self.onTimer)
    self.timer.start()
    self.props = QWidget()
    self.canvas = MyMplCanvas(dpi = 72,width = 8,height = 4)
    splitter.addWidget(self.canvas)
    splitter.addWidget(self.props)
    propLayout = QGridLayout()
    self.xNames = QComboBox()
    self.addButton = QPushButton("Add Line")
    self.clearButton = QPushButton("Clear Plot")
    self.yNames = QComboBox()

    playout = QBoxLayout(QBoxLayout.LeftToRight)
    playout.addWidget(QLabel("X variable"))
    playout.addWidget(self.xNames)
    playout.addWidget(QLabel("Y variable"))
    playout.addWidget(self.yNames)
    playout.addStretch()
    playout.addWidget(self.addButton)
    playout.addWidget(self.clearButton)
    
    self.connect(self.addButton,SIGNAL("clicked()"),self.addPlot)
    self.connect(self.clearButton,SIGNAL("clicked()"),self.clearPlots)
    layout.addWidget(splitter)
    
    
    self.plotList = QTreeWidget()
    self.lineStyles = QComboBox()
    self.lineStyles.addItem("line","line")
    self.lineStyles.addItem("scatter","scatter")
    self.lineStyles.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)

    self.plotList.setColumnCount(4)
    self.plotList.setHeaderLabels(("Datacube","X variable","Y variable","style"))

    removeButton = QPushButton("Remove line")
    removeButton.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)

    styleLabel = QLabel("Line style")
    styleLabel.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)

    linePropertiesLayout = QBoxLayout(QBoxLayout.LeftToRight)
    linePropertiesLayout.addWidget(styleLabel)
    linePropertiesLayout.addWidget(self.lineStyles)
    linePropertiesLayout.addWidget(removeButton)
    linePropertiesLayout.insertStretch(2)

    self.connect(removeButton,SIGNAL("clicked()"),self.removeLine)
    self.connect(self.plotList,SIGNAL("currentItemChanged(QTreeWidgetItem *,QTreeWidgetItem *)"),self.lineSelectionChanged)
    self.connect(self.lineStyles,SIGNAL("currentIndexChanged(int)"),self.updateLineStyle)

    propLayout.addLayout(playout,0,0)
    propLayout.addWidget(self.plotList,1,0)

    propLayout.addItem(linePropertiesLayout,2,0)

    self.props.setLayout(propLayout)
    self.setLayout(layout)
    
  def removeLine(self):
    self._currentIndex = self.plotList.indexOfTopLevelItem(self.plotList.currentItem())
    if self._currentIndex == -1 or self._currentIndex >= len(self._plots):
      return
    del self.canvas.axes.lines[self._currentIndex]
    del self._plots[self._currentIndex]
    self.plotList.takeTopLevelItem(self._currentIndex)
    self._currentIndex = None
    self.updatePlot(clear = True)
    
  def updateLineStyle(self,index):
    self._currentIndex = self.plotList.indexOfTopLevelItem(self.plotList.currentItem())
    if self._currentIndex == -1:
      return
    style = str(self.lineStyles.itemData(index).toString())
    if self._plots[self._currentIndex].style == style:
      return
    if style == 'scatter':
      self._plots[self._currentIndex].lines.set_linestyle('')
      self._plots[self._currentIndex].lines.set_marker('o')
    else:
      self._plots[self._currentIndex].lines.set_linestyle('-')
      self._plots[self._currentIndex].lines.set_marker('')
    self._plots[self._currentIndex].style = style
    self.updatePlot()
    self._plots[self._currentIndex].item.setText(3,style)
    
  def updateLineProperties(self,index):
    if index < len(self._plots):
      self.lineStyles.setCurrentIndex(self.lineStyles.findData(self._plots[index].style))
    
  def lineSelectionChanged(self,selected,previous):
    if selected != None:
      index = self.plotList.indexOfTopLevelItem(selected)
      self._currentIndex = index
      self.updateLineProperties(index)


class DataTreeView(QTreeWidget,ObserverWidget):
    
  def __init__(self,parent = None):
    QTreeWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self._root = None
    self._items = dict()
    self._manager = dm.DataManager()
    self.setMinimumWidth(300)
    self.setHeaderLabels(["Name"])
   
  def ref(self,datacube):
    return weakref.ref(datacube)
    
  def addDatacube(self,datacube,parent):
    item = QTreeWidgetItem()
    item.setText(0,str(datacube.name()))
    item._cube = weakref.ref(datacube)
    datacube.attach(self)
    self._items[self.ref(datacube)]= item
    if parent == self._root:
      self.insertTopLevelItem(0,item)
    else:
      self._items[self.ref(parent)].addChild(item)
    for child in datacube.allChildren():
      self.addDatacube(child,datacube)
      
  def removeItem(self,item):
    if item.parent() == None:
      self.takeTopLevelItem(self.indexOfTopLevelItem(item))
    else:
      item.parent().removeChild(item)  
  
  def removeDatacube(self,parent,datacube):
    if parent == self._root:
      item = self._items[self.ref(datacube)]
      self.takeTopLevelItem(self.indexOfTopLevelItem(item))
    else:
      item = self._items[self.ref(parent)]
      child = self._items[self.ref(datacube)]
      item.takeChild(item.indexOfChild(child))
    del self._items[self.ref(datacube)]
    datacube.detach(self)
    
  def updateDatacube(self,cube):
    item = self._items[self.ref(cube)]
    extraText = ""
    if cube == self._manager.master():
      extraText="[master]"
    item.setText(0,cube.name()+extraText)          
  
  def setRoot(self,root):
    self._root = root
    root.attach(self)
    self.initTreeView()
    
  def initTreeView(self):
    self.clear()
    for child in self._root.allChildren():
      self.addDatacube(child,self._root)
    
  def updatedGui(self,subject,property = None,value = None):
    if property == "addChild":
      child = value
      child.attach(self)
      self.addDatacube(child,subject)
    if property == "name" or property == "isMaster":
      self.updateDatacube(subject)
    if property == "removeChild":
      self.removeDatacube(subject,value)

class DatacubeProperties(QWidget,ObserverWidget):
  
  def updateBind(self):
    name = str(self.bindName.text())
    if name != None and self._codeRunner != None:
      print "Binding to local variable..."
      self._codeRunner.gv()[name] = self._cube
        
  
  def __init__(self,parent = None,codeRunner = None):
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    layout = QGridLayout()
    
    self._cube = None
    self._codeRunner = codeRunner
    self.name = QLineEdit()
    self.filename = QLineEdit()
    self.filename.setReadOnly(True)
    self.tags = QLineEdit()
    self.description = QTextEdit()
    self.parameters = QTextEdit()
    self.bindName = QLineEdit()
    self.updateBindButton = QPushButton("Update / Set")
    self.updateBindButton.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
    self.names = QListWidget()
    
    self.connect(self.updateBindButton,SIGNAL("clicked()"),self.updateBind)
    
    layout.addWidget(QLabel("Name"))
    layout.addWidget(self.name)
    layout.addWidget(QLabel("Filename"))
    layout.addWidget(self.filename)
    layout.addWidget(QLabel("Bind to local variable:"))
    bindLayout = QBoxLayout(QBoxLayout.LeftToRight)
    bindLayout.addWidget(self.bindName)
    bindLayout.addWidget(self.updateBindButton)
    layout.addItem(bindLayout)
    layout.addWidget(QLabel("Tags"))
    layout.addWidget(self.tags)
    layout.addWidget(QLabel("Description"))
    layout.addWidget(self.description)
    layout.addWidget(QLabel("Parameters"))
    layout.addWidget(self.parameters)
    layout.addWidget(QLabel("Variable names"))
    layout.addWidget(self.names)
    
    self.connect(self.name,SIGNAL("textEdited(QString)"),self.nameChanged)
    self.connect(self.tags,SIGNAL("textEdited(QString)"),self.tagsChanged)
    self.connect(self.description,SIGNAL("textChanged()"),self.descriptionChanged)
    self.setLayout(layout)
        
  def descriptionChanged(self):
    if self._cube == None:
      return
    if self._cube.description() != self.description.toPlainText():
      self._cube.setDescription(self.description.toPlainText())
    
  def nameChanged(self,text):
    if self._cube == None:
      return
    self._cube.setName(self.name.text())

  def namesChanged(self,names):
    self.names.clear()
    for name in names:
      self.names.addItem(name)

  def tagsChanged(self,text):
    if self._cube == None:
      return
    self._cube.setTags(self.tags.text())

  def updatedGui(self,subject = None,property = None,value = None):
    if subject == self._cube:
      if property == "names":
        self.namesChanged(value)
    
  def setDatacube(self,cube):
    if not self._cube == None:
      self._cube.detach(self)
    self._cube = cube
    self._cube.attach(self)
    self.updateProperties()
    
  def updateProperties(self):
    if self._cube == None:
      return
    self.filename.setText(str(self._cube.filename()))
    self.name.setText(str(self._cube.name()))
    self.tags.setText(str(self._cube.tags()))
    self.description.setPlainText(str(self._cube.description()))
    self.parameters.setPlainText(str(self._cube.parameters()))
    self.names.clear()
    for name in sorted(self._cube.names()):
      self.names.addItem(name)
  

#This is a frontend for the data manager class.
class DataManager(QMainWindow,ReloadableWidget,ObserverWidget):
  
  def selectCube(self,current,last):
    if not current == None:
      self._cube = current._cube()
      if self._cube == None:
        self.datacubeList.removeItem(current)
        return
      self.props.setDatacube(current._cube())
      self.datacubeViewer.setDatacube(current._cube())
      self.dataPlotter2D.setDatacube(current._cube())
      self.props.setEnabled(True)
      self.dataPlotter2D.setEnabled(True)
    else:
      self.props.setEnabled(False)
      self.dataPlotter2D.setEnabled(False)
    

  def updatedGui(self,subject = None,property = None,value = None):
    pass
  
  def loadDatacube(self):
    filename = QFileDialog.getOpenFileName()
    if not filename == '':
      cube = Datacube()
      cube.loadtxt(str(filename))
      self.manager.addDatacube(cube,atRoot = True)    

  def removeCube(self):
    if self._cube == None or self._cube.parent() == None:
      return
    self._cube.parent().removeChild(self._cube)
    self._cube = None
    print "Removed datacube..."
    
  def addCube(self):
    manager = dm.DataManager()
    cube = Datacube()
    cube.set(a = 44,b = 56754, c = 3)
    cube.commit()
    manager.addDatacube(cube)

  def saveCubeAs(self):
    self.saveCube(saveAs = True)
        
  def setAsMaster(self):
    if self._cube == None:
      return
    manager = dm.DataManager()
    manager.setMaster(self._cube)

  def saveCube(self,saveAs = False):
    if self._cube == None:
      return
    if self._cube.filename() == None or saveAs:
      filename = QFileDialog.getSaveFileName()
      if filename != "":
        self._cube.savetxt(str(filename))
    else:
      self._cube.savetxt()
  
  def __init__(self,parent = None,codeRunner = None):
    QMainWindow.__init__(self,parent)
    ReloadableWidget.__init__(self)
    ObserverWidget.__init__(self)
    self.setWindowTitle("Data Manager")
    self.setAttribute(Qt.WA_DeleteOnClose,True)
    self._codeRunner = codeRunner
    layout = QGridLayout()
    self.manager = dm.DataManager()
    self.datacubeList = DataTreeView()
    self.datacubeViewer = DatacubeTableView()
    self.datacubeList.setRoot(self.manager.root())
    self.connect(self.datacubeList,SIGNAL("currentItemChanged(QTreeWidgetItem *,QTreeWidgetItem *)"),self.selectCube)
    self.dataPlotter2D = Plot2DWidget()
    self.dataPlotter3D = Plot3DWidget()
    self.tabs = QTabWidget() 
    self._cubes = []
    self._cube = None
    
    leftLayout = QGridLayout()
    
    leftLayout.addWidget(self.datacubeList)
    
    layout.addLayout(leftLayout,0,0)
    layout.addWidget(self.tabs,0,1)
    menubar = self.menuBar()
    filemenu = menubar.addMenu("File")
    loadDatacube = filemenu.addAction("Load Datacube")
    self.connect(loadDatacube,SIGNAL("triggered()"),self.loadDatacube)
    menubar.addMenu(filemenu)
    
    widget = QWidget()
    widget.setLayout(layout)
    
    self.setCentralWidget(widget)
    self.props = DatacubeProperties(codeRunner = codeRunner)
    self.manager.attach(self)

    self.addButton = QPushButton("Add datacube")
    self.saveButton = QPushButton("Save")
    self.saveAsButton = QPushButton("Save As...")
    self.setAsMasterButton = QPushButton("Set as master")
    self.removeButton = QPushButton("Remove datacube")

    self.connect(self.addButton,SIGNAL("clicked()"),self.addCube)
    self.connect(self.saveButton,SIGNAL("clicked()"),self.saveCube)
    self.connect(self.saveAsButton,SIGNAL("clicked()"),self.saveCubeAs)
    self.connect(self.setAsMasterButton,SIGNAL("clicked()"),self.setAsMaster)
    self.connect(self.removeButton,SIGNAL("clicked()"),self.removeCube)

    boxLayout = QBoxLayout(QBoxLayout.LeftToRight)
    boxLayout.addWidget(self.addButton)
    boxLayout.addWidget(self.removeButton)
    boxLayout.addWidget(self.saveButton)
    boxLayout.addWidget(self.saveAsButton)
    boxLayout.addWidget(self.setAsMasterButton)
    boxLayout.addStretch()

    leftLayout.addLayout(boxLayout,1,0)

    self.tabs.addTab(self.props,"Properties")
    self.tabs.addTab(self.dataPlotter2D,"2D Data Plotting")
    self.tabs.addTab(self.dataPlotter3D,"3D Data Plotting")
    self.tabs.addTab(self.datacubeViewer,"Table View")
    self.selectCube(None,None)
