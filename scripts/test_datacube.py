cube = Datacube()
cube.loadtxt(r"l:\local-expdata\ad1-b6\2010_10_19\cavity_2\Cavity Anticrossing - Cavity 1-12.par")
##
import time
start = time.time()
import sys
if 'pyview.lib.datacube' in sys.modules:
	reload(sys.modules['pyview.lib.datacube'])
from pyview.lib.datacube import *
cube.save("test2.dat")
newcube = Datacube()
newcube.load("test2.dat")

if cube != newcube:
	print "Error! Cubes are not equal!"
else:
	print "Cubes are equal!"

print "Elaspsed time: %g s" % (time.time()-start)