import sys

import os
import os.path

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from lib.ramps import *

ramp = ParameterRamp()
ramp.setGenerator("ramp = [1,2,3]")
ramp.setCode("data.set(fcav = x)")

ramp2 = ParameterRamp()
ramp2.setGenerator("""
from numpy import *
ramp = arange(0,10,0.1)
""")

ramp.addChild(ramp2)

subramp = MeasurementRamp()
subramp.setCode("""
print 'Doing some measurement...'
data.set(test = 4,other = 5.4)
""")

ramp2.addChild(subramp)

subramp = MeasurementRamp()
subramp.setCode("""
print 'Doing some other measurement.'
cube = Datacube()
cube.set(y = 5.4)
cube.commit()
cube.set(z = 3.0, y = 4.3)
cube.commit()
data.addChild(cube)
""")

ramp.addChild(subramp)

cube = Datacube()

backup = ramp.tostring()

loaded = Ramp()
loaded = loaded.fromstring(backup)
loaded.run(cube)

print cube.childrenAt(0)[1].table()
print cube.structure()
print cube.names()
print cube.table()
