import sys
import os
import os.path

global params
params = dict()

globalVariables = dict()
localVariables = dict()

params['path'] = os.path.dirname(os.path.abspath(__file__+"/.."))
params['dataPath'] = r"L:\local-expdata"
params['setupPath'] = params['dataPath']+r"\qubit setup\instrument setups"
params['calibrationPath'] = params['dataPath']+r"\qubit setup\calibration"
params['calibrationPath.iqmixer'] = params['dataPath']+r"\qubit setup\calibration"
params['directories.crystalIcons'] = '/ide/data/icons/crystal/crystal_project/16x16'
params['directories.famfamIcons'] = '/ide/data/icons/famfam/icons/'

print "Parameters loaded."