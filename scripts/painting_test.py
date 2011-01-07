import sys

import os
import os.path

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from scripts.xyplot import *

app = QApplication(sys.argv)
MyWindow = QMainWindow()
Label = XYPlot()
MyWindow.setCentralWidget(Label)


MyWindow.show()

app.exec_()