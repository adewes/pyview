import sys
import math

from pyview.ide.datamanager import *
from pyview.ide.dataviewer import *
import pyview.helpers.datamanager as dm
from pyview.lib.datacube import *

if __name__ == "__main__":
  app = QApplication(sys.argv)
  manager = dm.DataManager()
  cube = Datacube()
  dv = DataViewer()
  dv.show()
  cube.set(x= 0, y= 1)
  child = Datacube()
  for i in range(0,100):
    child.set(a = i,b = i*i,c = math.sin(i*0.5)*i*i)
    child.commit()
  child.setName("child cube")
  cube.addChild(child)
  cube.commit()
  manager.addDatacube(cube)
  print manager.datacubes()
  tool = DataManager()
  tool.show()
  sys.exit(app.exec_())
