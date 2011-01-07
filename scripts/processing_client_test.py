import sys
import os
import multiprocessing
from multiprocessing.managers import SyncManager

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

if __name__ == "__main__":

  manager = SyncManager(address=('localhost', 50000), authkey='abc')
  manager.register('get_manager')
  manager.connect()
  m = manager.get_manager()
  m.
  temp = m.instrument("temperature")
  print temp
  print temp.temperature()