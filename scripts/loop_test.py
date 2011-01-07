import sys

import os
import os.path

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from ide.loop import *

app = QApplication(sys.argv)
MyWindow = Loop()
MyWindow.show()

app.exec_()