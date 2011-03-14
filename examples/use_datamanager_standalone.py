from pyview.ide.datamanager import startDataManagerThread
from pyview.lib.datacube import *
from pyview.helpers.datamanager import DataManager

if __name__ == '__main__':
  #This launches the graphical frontend of the data manager
  startDataManagerThread()
  #This returns a reference to the actual data manager (which is a Singleton)
  dataManager = DataManager()
  
  #We create some data...
  data = Datacube("testdata")
  
  #We add the datacube to the data manager.
  dataManager.addDatacube(data)
  
  #We add some data...
  for i in range(0,100):
    data.set(x = i,y = i*i,z = sqrt(i))
    data.commit()