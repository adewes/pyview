import sys
import os
import multiprocessing
from multiprocessing.managers import SyncManager

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from helpers.instrumentsmanager import *

print "Initializing instruments..."

MyManager = Manager()

#The temperature
temperature = MyManager.getInstrument("temperature")

print temperature.temperature()
if __name__ == "__main__":

  manager = SyncManager(address=('localhost', 50000), authkey='abc')
  manager.register('get_manager', callable=lambda:MyManager)
  server = manager.get_server()
  server.serve_forever()