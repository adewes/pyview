import sys

sys.path.append('.')
sys.path.append('../')

from ide.dataviewer import *
import helpers.datamanager as dm
from lib.datacube import *

if __name__ == "__main__":
  app = QApplication(sys.argv)
  manager = dm.DataManager()
  cube = Datacube()
  for i in range(0,1000):
    cube.set(x= i*0.1, y= sin(i*0.01))
    cube.commit()
  manager.addDatacube(cube)
  tool = DataViewer(cube)
  tool.show()
  sys.exit(app.exec_())
