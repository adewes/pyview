import sys
import getopt
import os
import os.path
import weakref
import gc
import time

import pyview.helpers.datamanager as dm
from pyview.lib.datacube import *
from pyview.lib.classes import *
from pyview.lib.patterns import *
from pyview.ide.datacubeview import *
reload(sys.modules['pyview.ide.datacubeview'])
from pyview.ide.datacubeview import *
from pyview.ide.mpl.canvas import *
reload(sys.modules['pyview.ide.mpl.canvas'])
from pyview.ide.mpl.canvas import *
from pyview.ide.patterns import ObserverWidget

import numpy

def startPlugin(ide,*args,**kwargs):
  """
  This function initializes the plugin
  """
  if hasattr(ide,"instrumentsTab"):
    ide.tabs.removeTab(ide.tabs.indexOf(ide.instrumentsTab))
  instrumentsTab = InstrumentsPanel()
  ide.instrumentsTab = instrumentsTab
  ide.tabs.addTab(instrumentsTab,"Instruments")
  ide.tabs.setCurrentWidget(instrumentsTab)

plugin = dict()
plugin["name"] = "Data Manager"
plugin["version"] = "0.1"
plugin["author.name"] = "Andreas Dewes"
plugin["author.email"] = "andreas.dewes@gmail.com"
plugin["functions.start"] = startPlugin
plugin["functions.stop"] = None
plugin["functions.restart"] = None
plugin["functions.preferences"] = None


class Datacube2DPlot:
  
  def __init__(self):
    pass
    
class Plot3DWidget(QWidget,ObserverWidget):
  pass

class Plot2DWidget(QWidget,ObserverWidget):
  
  def nameSelector(self):
    box = QComboBox()
    box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
    names = self._cube.names()
    return box
    
  def updatePlot(self,clear = False):
    if len(self._plots) == 0:
      self.canvas.figure.clf()
      self.canvas.axes = self.canvas.figure.add_subplot(111)
      self.canvas.draw()
      return
    xnames = []
    ynames = []
    title = self._plots[0].cube.name()
    legend = []
    legendPlots = []
    filenames = []
    for plot in self._plots:
      if plot.xname != "[row number]":
        xvalues = plot.cube.column(plot.xname)
      else:
        xvalues = arange(0,len(plot.cube),1)
      if plot.yname != "[row number]":
        yvalues = plot.cube.column(plot.yname)
      else:
        yvalues = arange(0,len(plot.cube),1)

      plot.lines.set_xdata(xvalues)
      plot.lines.set_ydata(yvalues)
      if not plot.xname in xnames:
        xnames.append(plot.xname)
      if not plot.yname in ynames:
        ynames.append(plot.yname)
      if not plot.cube.filename() in filenames and plot.cube.filename() != None:
        legend.append(plot.yname+":"+plot.cube.filename()[:-4])
        legendPlots.append(plot.lines)
        filenames.append(plot.cube.filename())
      #This is a bug in matplotlib. We have to call "recache" to make sure that the plot is correctly updated.
      plot.lines.recache()
    if self.canvas.axes.get_autoscale_on() == True:
      self.canvas.axes.relim()
      self.canvas.axes.autoscale_view()

    self.canvas.axes.set_xlabel(", ".join(xnames))
    self.canvas.axes.set_ylabel(", ".join(ynames))
    self.canvas.axes.set_title(title)
    if self._showLegend and len(legend) > 0:
      from matplotlib.font_manager import FontProperties
      self.canvas.axes.legend(legendPlots,legend,prop = FontProperties(size = 6))
    else:
      self.canvas.axes.legend_ = None 
    self.canvas.draw()

  def addPlot(self,xName=None,yName=None,**kwargs):
    plot = Datacube2DPlot()
    if xName==None and yName==None:
      plot.xname = str(self.xNames.currentText())
      plot.yname = str(self.yNames.currentText())
    else:
      plot.xname = xName
      plot.yname = yName

    if self._cube == None:
      return

    if ((not plot.xname in self._cube.names()) and plot.xname != "[row number]") or ((not plot.yname in self._cube.names())  and plot.yname != "[row number]"):
      return
    plot.cube = self._cube 
    plot.legend = "%s, %s vs. %s" % (self._cube.name(),plot.xname,plot.yname)
    plot.style = 'line'
    if plot.xname != "[row number]":
      xvalues = plot.cube.column(plot.xname)
    else:
      xvalues = arange(0,len(plot.cube),1)
    if plot.yname != "[row number]":
      yvalues = plot.cube.column(plot.yname)
    else:
      yvalues = arange(0,len(plot.cube),1)
    plot.lines, = self.canvas.axes.plot(xvalues,yvalues,**kwargs)
    self._cnt+=1
    plot.cube.attach(self)
    plot.lineStyleLabel = QLabel("line style") 
    self._plots.append(plot)
    
    plotItem = QTreeWidgetItem([self._cube.name(),plot.xname,plot.yname,"line"])
    self.plotList.addTopLevelItem(plotItem)
    self.plotList.setItemWidget(plotItem,4,plot.lineStyleLabel)
    self.plotList.update()
    plot.item=plotItem
    self.updatePlot()
    
  def clearPlots(self):
    for plot in self._plots:
      if plot.cube != self._cube:
        plot.cube.detach(self)
    self._plots = []
    self._currentIndex = None
    self.plotList.clear()
    self._cnt = 0
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
    self.xNames.addItem("[row number]")
    self.yNames.addItem("[row number]")
    for name in sorted(names):
      self.xNames.addItem(name,name)    
      self.yNames.addItem(name,name)
      
  def updatedGui(self,subject = None,property = None,value = None):
    self._updated = False
    if property == "names":
      if subject == self._cube:
        self.updateNames(value)
      
  def onTimer(self):
    if self._updated == True:
      return
    self._updated = True
    self.updatePlot()
    
  def showLegendStateChanged(self,state):
    if state == Qt.Checked:
      self._showLegend = True
    else:
      self._showLegend = False
    self.updatePlot()

  def __init__(self,parent = None):
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self._cube = None
    self._showLegend = True
    self._plots = []
    self._cnt = 0
    self._lineColors = [(0,0,0),(0.8,0,0),(0.0,0,0.8),(0.0,0.5,0),(0.5,0.5,0.5),(0.8,0.5,0.0),(0.9,0,0.9)]
    self._lineStyles = ['-','--','-.',':']
    self._updated = False
    self.xnames = []
    self._currentIndex = None
    self.ynames = []
    self._plottedVariables =[]
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
    self.xNames.setSizeAdjustPolicy(QComboBox.AdjustToContents)
    self.addDefaultCurves=QPushButton("Autoplot")
    self.addButton = QPushButton("Add Curve")
    self.clearButton = QPushButton("Clear Plot")
    self.yNames = QComboBox()
    self.showLegend = QCheckBox("Show Legend")
    self.showLegend.setCheckState(Qt.Checked)
    self.yNames.setSizeAdjustPolicy(QComboBox.AdjustToContents)

    playout = QBoxLayout(QBoxLayout.LeftToRight)
    playout.addWidget(QLabel("X:"))
    playout.addWidget(self.xNames)
    playout.addWidget(QLabel("Y:"))
    playout.addWidget(self.yNames)
    playout.addWidget(self.addButton)
    playout.addWidget(self.showLegend)
    playout.addStretch()
    playout.addWidget(self.addDefaultCurves)
    playout.addWidget(self.clearButton)
    
    self.connect(self.showLegend,SIGNAL("stateChanged(int)"),self.showLegendStateChanged)
    self.connect(self.addDefaultCurves,SIGNAL("clicked()"),self.addDefaultPlot)
    self.connect(self.addButton,SIGNAL("clicked()"),self.addPlot)
    self.connect(self.clearButton,SIGNAL("clicked()"),self.clearPlots)
    layout.addWidget(splitter)
    
    self.plotList = QTreeWidget()
    self.lineStyles = QComboBox()
    self.lineStyles.addItem("line","line")
    self.lineStyles.addItem("scatter","scatter")
    self.lineStyles.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)

    self.plotList.setColumnCount(5)
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
  
  def addDefaultPlot(self):
    if 'defaultPlot' in self._cube.parameters():
      for params in self._cube.parameters()["defaultPlot"]:
        if len(params) == 3:
          (xName,yName,kwargs) = params
        else:
          (xName,yName) = params
          kwargs = {}
        found = False
        for plot in self._plots:
          if plot.xname == xName and plot.yname == yName and plot.cube == self._cube:
            found = True
            break
        if found:
          continue
        self.addPlot(xName=xName,yName=yName,**kwargs)

class DataTreeView(QTreeWidget,ObserverWidget):
    
  def __init__(self,parent = None):
    QTreeWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self._root = None
    self._items = dict()
    self._manager = dm.DataManager()
#    self.setMinimumWidth(200)
    self.setHeaderLabels(["Name"])
   
  def ref(self,datacube):
    return weakref.ref(datacube)

  def contextMenuEvent(self, event):    
    menu = QMenu(self)
    saveAsAction = menu.addAction("Save as...")
    removeAction = menu.addAction("Remove")
    action = menu.exec_(self.viewport().mapToGlobal(event.pos()))
    if action == saveAsAction:
      pass

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
    for child in datacube.children():
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
    for child in self._root.children():
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
    self.bindName = QLineEdit()
    self.updateBindButton = QPushButton("Update / Set")
    self.updateBindButton.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
    self.connect(self.updateBindButton,SIGNAL("clicked()"),self.updateBind)
    
    font = self.description.currentFont()
    font.setPixelSize(18)
    self.description.setFont(font  )
    
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


  def tagsChanged(self,text):
    if self._cube == None:
      return
    self._cube.setTags(self.tags.text())

  def updatedGui(self,subject = None,property = None,value = None):
    pass
      
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
    

#This is a frontend for the data manager class.
class DataManager(QMainWindow,ObserverWidget):
  
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
    filename = QFileDialog.getOpenFileName(filter = "Datacubes (*.par)")
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
        
  def markAsGood(self):
    if self._cube == None:
      return
    workingDir = os.getcwd()
    subDir = os.path.normpath(workingDir+"/good_data")
    if not os.path.exists(subDir):
      os.mkdir(subDir)
    if "goodData" in self._cube.parameters() and self._cube.parameters()["goodData"] == True:
      print "Already marked, returning..."
      return
    self._cube.savetxt(os.path.normpath(subDir+"/"+self._cube.name()))
    self._cube.parameters()["goodData"] = True
    messageBox = QMessageBox(QMessageBox.Information,"Data marked as good","The data has been marked and copied into the subfolder \"good_data\"")
    messageBox.exec_()

  def saveCube(self,saveAs = False):
    if self._cube == None:
      return
    if self._cube.filename() == None or saveAs:
      filename = QFileDialog.getSaveFileName(filter = "Datacubes (*.par)")
      if filename != "":
        self._cube.savetxt(str(filename))
    else:
      self._cube.savetxt()
  
  def __init__(self,parent = None,codeRunner = None):
    QMainWindow.__init__(self,parent)
    ObserverWidget.__init__(self)
    self.setWindowTitle("Data Manager")
    self.setAttribute(Qt.WA_DeleteOnClose,True)
    self._codeRunner = codeRunner
    splitter = QSplitter(Qt.Horizontal)
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
    
    leftWidget = QWidget()
    leftWidget.setLayout(leftLayout)
    
    splitter.addWidget(leftWidget)
    splitter.addWidget(self.tabs)
    menubar = self.menuBar()
    filemenu = menubar.addMenu("File")
    
    newDatacube = filemenu.addAction("New")
    loadDatacube = filemenu.addAction("Load")
    saveDatacube = filemenu.addAction("Save")
    saveDatacubeAs = filemenu.addAction("Save as...")
    removeDatacube = filemenu.addAction("Remove")
    filemenu.addSeparator()
    markAsGood = filemenu.addAction("Mark as Good")
    
    self.connect(loadDatacube,SIGNAL("triggered()"),self.loadDatacube)
    self.connect(newDatacube,SIGNAL("triggered()"),self.addCube)
    self.connect(saveDatacube,SIGNAL("triggered()"),self.saveCube)
    self.connect(saveDatacubeAs,SIGNAL("triggered()"),self.saveCubeAs)
    self.connect(removeDatacube,SIGNAL("triggered()"),self.removeCube)
    self.connect(markAsGood,SIGNAL("triggered()"),self.markAsGood)
    
    menubar.addMenu(filemenu)
    
    self.setCentralWidget(splitter)
    
    self.props = DatacubeProperties(codeRunner = codeRunner)
    self.manager.attach(self)

    self.tabs.addTab(self.props,"Properties")
    self.tabs.addTab(self.dataPlotter2D,"2D Data Plotting")
    self.tabs.addTab(self.dataPlotter3D,"3D Data Plotting")
    self.tabs.addTab(self.datacubeViewer,"Table View")
    self.selectCube(None,None)

def startDataManagerThread():
  thread = DataManagerThread()
  thread.setDaemon(False)
  thread.start()

def startDataManager(qApp = None):
  if qApp == None:
    qApp = QApplication(sys.argv)
  qApp.setStyle(QStyleFactory.create("QMacStyle"))
  qApp.setStyleSheet("""
QTreeWidget:Item {padding:6;}
QTreeView:Item {padding:6;}
  """)
  qApp.connect(qApp, SIGNAL('lastWindowClosed()'), qApp,
                    SLOT('quit()'))
  dataManager = DataManager()
  dataManager.show()
  qApp.exec_()
  
  print "Exiting..."
  
class DataManagerThread(threading.Thread):

  def __init__(self):
    threading.Thread.__init__(self)

  def run(self):
    startDataManager(None)
          
if __name__ == '__main__':
  starDataManagerThread()