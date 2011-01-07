import sys

import os
import os.path

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from scripts.qubit.calibration.jba import *

calibrator = JBACalibration()
calibrator.sayHi()
sys.stdin.readline()
calibrator.reloadClass()
calibrator.sayHi()
