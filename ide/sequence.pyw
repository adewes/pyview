from pyview.lib.classes import *

class Sequence(QWidget):


  def __init__(self,sequence):
    QWidget.__init__(self)
    self.layout = QGridLayout()
    self._sequence = sequence
    
    stopButton = QPushButton("Stop")
    pauseButton = QPushButton("Pause")
    resumeButton = QPushButton("Resume")
    
    boxLayout = QBoxLayout(QBoxLayout.LeftToRight)

    self.layout.addWidget(QLabel("Sequence generator"))
    
    boxLayout.addWidget(pauseButton)
    boxLayout.addWidget(resumeButton)
    boxLayout.addWidget(pauseButton)
    
    self.layout.addLayout(boxLayout,0,1)

    setSequence = QPushButton("Update sequence")
    
    self.setLayout(self.layout)

