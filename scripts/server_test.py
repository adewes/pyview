from classes import *

acqiris_board = RemoteInstrument()

acqiris_board.startServer()

acqiris_board.connect('127.0.0.1',int(sys.argv[1]))

while 1:
  pass