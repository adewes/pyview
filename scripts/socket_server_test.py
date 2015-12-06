"""
This is a small script that exposes a remote instrument manager via a TCP/IP connection.
"""

import socket
import threading
import pickle
from struct import *
import SocketServer
import numpy
import time

import sys
import os
import weakref

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.dirname(os.path.realpath(__file__+"\\..\\..")))

DEBUG = False

from pyview.helpers.instrumentsmanager import *
from pyview.lib.classes import *

MyManager = Manager()


class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    manager = None

    def handle(self):
      lendata = self.request.recv(4)
      if len(lendata) == 0:
        return None
      length = unpack("l",lendata)[0]
      received = self.request.recv(length)
      binary = received
      while len(received)>0 and len(binary) < length:
        received = self.request.recv(length-len(binary))
        binary+=received
      m = Command().fromString(binary)
      if m == None:
        return
      if DEBUG:
        print "Received command: {0!s}".format(m.name())
      if hasattr(self.manager,m.name()):
        method = getattr(self.manager,m.name())
        try:
          result = method(*m.args(),**m.kwargs())
          returnMessage = Command(name = "return",args = [result])
          self.request.send(returnMessage.toString())
        except Exception as exception:
          print "An exception occured:{0!s}".format(str(exception))
          print "args: {0!s}".format(str(m.args()))
          print "kwargs: {0!s}".format(str(m.kwargs()))
          returnMessage = Command(name = "exception",args = [exception])
          self.request.send(returnMessage.toString())

ThreadedTCPRequestHandler.manager = RemoteManager(MyManager)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

def client(ip, port, message):
    conn  = ServerConnection(ip,port)
    print conn.instrument("qubit1mwg","anritsu_mwg",[],{},False)
    for i in range(0,10):
      print conn.dispatch("qubit1mwg","frequency")

if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    if len(sys.argv) >= 2:
      hostname = sys.argv[1]
    else:
      hostname = "localhost"
    HOST, PORT = hostname, 8000
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address
  
    print "Running on ip {0!s}, port {1:d}".format(ip, port)

    server_thread = threading.Thread(target=server.serve_forever)

    server_thread.setDaemon(True)
    server_thread.start()
    print "Server loop running in thread:", server_thread.getName()

    while True:
      try:
        time.sleep(1)
      except KeyboardInterrupt:
        break
    print "Shutting down..."
    server.shutdown()