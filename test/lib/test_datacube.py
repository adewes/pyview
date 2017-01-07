
import unittest
import shutil
import numpy
import os.path

from pyview.lib.datacube import Datacube

import random

class TestDatacubeManipulation(unittest.TestCase):

  """
  Tests the data manipulation functions of the datacube class.
  """
  
  def setUp(self):
    self._cube = Datacube()
    self._cube.addVariables(["x","y","z"])
  
  def tearDown(self):
    pass
    
  def test_set(self):
    pass
    
  def test_commit(self):
    pass
    
  def test_get_column(self):
    pass
    
  def test_create_column(self):
    pass
    
  def test_goto(self):
    pass
    
  def test_insert(self):
    pass
    
  def test_description(self):
    pass
    
  def test_name(self):
    pass
    
  def test_tags(self):
    pass
    
  def test_parameters(self):
    pass
    
  def test_table_geometry(self):
    pass
    
  def test_children(self):
    pass
    
  def test_addRoles(self):
    roles = ["somerole","anotherrole"]
    self._cube.addRoles("x",roles)
    self.assertEqual(self._cube.roles("x"),roles)
    
  def test_setRoles(self):
    roles = ["somerole","anotherrole"]
    self._cube.addRoles("x",["garbage"])
    self._cube.setRoles("x",roles)
    self.assertEqual(self._cube.roles("x"),roles)
    
  def test_variablesWithRoles(self):
    self._cube.setRoles("x",["1","2","3"])
    self._cube.setRoles("y",["2","3","4"])
    self._cube.setRoles("z",["3","4","5"])
    
    self.assertEqual(self._cube.variablesWithRoles(["1"]),["x"])
    self.assertEqual(self._cube.variablesWithRoles(["2"]),["x","y"])
    self.assertEqual(self._cube.variablesWithRoles(["3"]),["x","y","z"])
    self.assertEqual(self._cube.variablesWithRoles(["3","4"]),["y","z"])
    self.assertEqual(self._cube.variablesWithRoles(["3","4","5"]),["z"])
    
class TestDatacubeIO(unittest.TestCase):

  """
  Tests the IO functions of the datacube class.
  """
  
  def setUp(self):

    """
    We create all necessary directories and test datacubes for the IO tests.
    """
  
    self.testCubes = dict()
    rc = Datacube()
    
    self.testCubes["real"] = rc
    
    rc.setName("Datacube test: Real data")
    rc.setParameters({"test":1,"array":[1,2,3,4],"hash":{"a":1,"b":2}})
    for i in range(0,2):
      rc.set(x = i,y = i*i, z = i*i*i,r = random.random())
      child = Datacube()
      child.setName("test {0:d}".format(i))
      rc.addChild(child)
      rc.commit()
      for j in range(0,2):
        child.set(x = j,t = j*2-j*j,r = random.random())
        child.commit()
    
    self.dataPath = os.path.normpath(os.path.dirname(__file__)+"/data")
    
    if not os.path.exists(self.dataPath):
      os.mkdir(self.dataPath)
        
    cx = Datacube(dtype = numpy.complex128)
        
    self.testCubes["complex"] = cx
    
    rc.setName("Datacube test: Complex data")
    rc.setParameters({"test":1,"array":[1,2,3,4],"hash":{"a":1,"b":2}})
    for i in range(0,2):
      cx.set(x = i,y = i*i*1j+4, z = i*i*i*1j,r = 1j*random.random())
      child = Datacube(dtype = numpy.complex128)
      child.setName("test {0:d}".format(i))
      cx.addChild(child)
      cx.commit()
      for j in range(0,2):
        child.set(x = j,t = j*2-j*j*1j,r = 1j*random.random())
        child.commit()
        
  
  def tearDown(self):
    shutil.rmtree(self.dataPath,ignore_errors = True)

  def test_saveToHdf5(self):
    """
    Test saving a datacube to a HDF5 file
    """
    for key in self.testCubes.keys():
      print "Checking HDF5 loading of test cube {0!s}".format(key)
      cube = self.testCubes[key]
      filename = os.path.normpath(self.dataPath+"/test_{0!s}.hdf5".format(key))
      cube.saveToHdf5(filename,overwrite = True)
      
      self.assert_(os.path.exists(filename),"File {0!s} has not been created!".format(filename))
      self.assert_(os.path.isfile(filename))
      
      restoredCube = Datacube()
      restoredCube.loadFromHdf5(filename)
      
      self.assert_(restoredCube.equal(cube),"Error: Restored datacube does not match original one!")
     
  def test_savetxt(self):
    """
    Test saving a datacube to a text file
    """
    for key in self.testCubes.keys():
      print "Checking plain text loading of test cube {0!s}".format(key)
      cube = self.testCubes[key]
      filename = os.path.normpath(self.dataPath+"/test_{0!s}.txt".format(key))
      cube.savetxt(filename,overwrite = True)
      
      self.assert_(os.path.exists(filename),"File {0!s} has not been created!".format(filename))
      self.assert_(os.path.isfile(filename))
      
      restoredCube = Datacube()
      restoredCube.loadtxt(filename)
            
      self.assert_(restoredCube.equal(cube),"Error: Restored datacube does not match original one!")
          
  def test_save(self):
    """
    Test saving a datacube to a binary file
    """
    for key in self.testCubes.keys():
      print "Checking binary loading of test cube {0!s}".format(key)
      cube = self.testCubes[key]
      filename = os.path.normpath(self.dataPath+"/test_{0!s}.dat".format(key))
      cube.save(filename)
      
      self.assert_(os.path.exists(filename),"File {0!s} has not been created!".format(filename))
      self.assert_(os.path.isfile(filename))
      
      restoredCube = Datacube()
      restoredCube.load(filename)
            
      self.assert_(restoredCube.equal(cube),"Error: Restored datacube does not match original one!")
          