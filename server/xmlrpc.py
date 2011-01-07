from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

import SocketServer

import sys
import os
import weakref

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from helpers.instrumentsmanager import *

#The temperature


class AsyncXMLRPCServer(SocketServer.ThreadingMixIn,SimpleXMLRPCServer): pass

class MyFuncs:
    def div(self, x, y):
        return x // y

if __name__ == '__main__':
  MyManager = Manager()
  server = AsyncXMLRPCServer(("localhost", 8000),
                            requestHandler=RequestHandler,allow_none = True)
  server.register_introspection_functions()
  server.register_instance(RemoteInstrumentManager(MyManager))

  server.serve_forever()
