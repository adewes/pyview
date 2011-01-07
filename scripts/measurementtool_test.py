import sys

sys.path.append('.')
sys.path.append('../')

from ide.measurementtool import *
from ide.datamanager import *
from ide.dataviewer import *

if __name__ == "__main__":
  app = QApplication(sys.argv)
  tool = MeasurementTool()
  tool.show()
  manager = DataManager()
  manager.show()
  viewer = DataViewer()
  viewer.show()
  sys.exit(app.exec_())
