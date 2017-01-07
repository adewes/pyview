import sys

import os
import os.path

from pyview.lib.datacube import *

def generateSubcube(level = 0):
  print "Generating subcube at level {0:d}".format(level)
  subcube = Datacube()
  mlist = []
  cnt = 0 
  for fmw in range(0,1000):
    cnt+=1
    if cnt % 2 == 0:
      mlist.append(fmw * fmw)
    subcube.set(fmw = fmw)
    subcube.set(psw = fmw *0.1,somethingelse = 3.45,anothervar = 5433.33)
    if level > 0 and fmw < 10:
      subcube.addChild(generateSubcube(level-1))
    subcube.commit()
  subcube.createColumn("addedrow",mlist)
  subcube.goTo(4)
  subcube.set(newvariable = 4444)
  subcube.commit()
  subcube.set(unknownvar = 42)
  params = dict()
  params['test'] = {"anothertest":4,"something":5}
  params['new'] = 4.5
  params['string'] = "this is just a test!!!"
  subcube.setParameters(params)
  subcube.commit()
  return subcube

cube = generateSubcube(1)
cube2 = generateSubcube(0)
cube.attach(cube2)
cube2.attach(cube)
print "Original cube:"
print cube.names()
print cube.children()
print cube.len()
print shape(cube.table())
print cube.structure()
print "Saving to text..."
cube.savetxt("test",overwrite = True)
cube.setName("test2")
cube.savetxt()
print "Saving to binary..."
print cube.save("binary.dat")
print "Done..."
#print len(saved)/1024/1e3
cube = Datacube()
cube.loadtxt("test")
bcube = Datacube()
bcube = bcube.load("binary.dat")
print "New cube:"
print cube.names()
print cube.children()
print cube.len()
print shape(cube.table())
print cube.structure()
print "New binary cube:"
print bcube.names()
print bcube.children()
print bcube.len()
print shape(bcube.table())
print bcube.structure()
if bcube != cube:
  print "Error!"
print "Done..."