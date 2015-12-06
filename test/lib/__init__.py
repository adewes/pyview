#+
# 
# This file is part of h5py, a low-level Python interface to the HDF5 library.
# 
# Copyright (C) 2008 Andrew Collette
# http://h5py.alfven.org
# License: BSD  (See LICENSE.txt for full license)
# 
# $Date$
# 
#-

import pyview.test.lib
import unittest

mnames = [
'test_datacube'
]

def runtests():

    ldr = unittest.TestLoader()
    suite = unittest.TestSuite()
    modules = [__import__('pyview.test.lib.'+x, fromlist=[pyview.test]) for x in mnames]
    for m in modules:
        suite.addTests(ldr.loadTestsFromModule(m))

    runner = unittest.TextTestRunner()
    return runner.run(suite)

def autotest():
    try:
        if not runtests():
            sys.exit(17)
    except:
        sys.exit(2)

def testinfo():
    print "{0:d} tests disabled".format(common.skipped)
    
if __name__ == '__main__':
  runtests()




