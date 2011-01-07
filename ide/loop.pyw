from lib.classes import *
from ide.params import *
from ide.codeeditor import *
from scripts.xyplot import *

class Loop(QWidget):

  def updateRamp(self):
    print "Updating ramp"
    code = str(self.scriptEditor.toPlainText())
    print "Evaluating code:" + code
    localVars = {'ramp' : list()}
    exec(code,globals(),localVars)
    self.ramp = localVars['ramp']
    self.redrawRamp()
    
  def redrawRamp(self):
    self.canvas.clear()
    self.canvas.addData(range(0,len(self.ramp)),self.ramp)
    
  def plotOnMouseMove(self,e):
    if e.inaxes:
      self.selectedIndex = int(e.xdata)
      self.redrawRamp()

  def __init__(self):
    QWidget.__init__(self)
    self.layout = QGridLayout()
    self.selectedIndex = None
    self.canvas = XYPlot()
    self.canvas.setMinimumSize(300,200)
    self.ramp = arange(0,1000,10)
    self.redrawRamp()
    self.setFixedSize(400,400)
    
    self.toolbar = QToolBar()
    startIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/player_start.png')
    stopIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/player_stop.png')
    pauseIcon = QIcon(params['path']+params['directories.crystalIcons']+'/actions/player_pause.png')

    start = self.toolbar.addAction(startIcon,"Run")
    stop = self.toolbar.addAction(stopIcon,"Stop Loop")
    pause = self.toolbar.addAction(pauseIcon,"Pause Loop")
    
    self.scriptEditor = CodeEditor()
    self.scriptEditor.activateHighlighter()
        
    updateButton = QPushButton("Update")
    updateButton.setFixedWidth(100)
    
    self.connect(updateButton,SIGNAL("clicked()"),self.updateRamp)
    
    self.layout.addWidget(self.canvas)
    self.layout.addWidget(QLabel("Sequence generator"))
    self.layout.addWidget(self.scriptEditor)
    self.layout.addWidget(updateButton)

    setSequence = QPushButton("Update sequence")
    
    self.setLayout(self.layout)

#    self.addToolBar(self.toolbar)