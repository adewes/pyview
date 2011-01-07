MyManager = helpers.instrumentsmanager.Manager()

yoko = MyManager.reloadInstrument("yokogawa","GPIB0::19")
yoko2 = MyManager.instrumentCopy("yokogawa","yoko2","GPIB0::19")
yoko2 = MyManager.reloadInstrument("yoko2","GPIB0::9")

acqiris2 = MyManager.getInstrument("acqiris_client")
acqiris2 = MyManager.reloadInstrument("acqiris_client","localhost")

acqiris = MyManager.instrumentCopy("acqiris_client","acqiris2","localhost")

acqiris2.setParameters([2,250,2,250,0,0,1,0,0,0])
acqiris.setParameters([2,250,2,250,0,0,2,0,0,0])

##
def attenuatorRangeCheck(range,Yoko,Acqiris,polarity = 1):
	ps = []
	max = 0
	maxVoltage = 0
	for i in range:
		print Yoko.setVoltage(i*polarity)
		segments = 2500
		points = 250
		value = Acqiris.AcquireV3(segments = segments,delay = 0)
		variance = (cov(value[points*4+segments:points*4+segments*2])+cov(value[points*4+segments*2:points*4+segments*3]))
		ps.append(variance)
		cla()
		plot(ps)
		if variance > max:
			max = variance
			maxVoltage = i
	return (ps,max,maxVoltage)

import numpy

def adjustRotation(Acqiris):
	import math
	segments = 2500
	points = 250
	value = Acqiris.AcquireV3(segments = segments,delay = 0)
	covar = numpy.cov(value[points*4+segments:points*4+segments*2],value[points*4+segments*2:points*4+segments*3])
	angle = math.atan2(covar[0,1],covar[0,0])
	print angle*180.0/numpy.pi

def adjustOffset(Acqiris):
	pass

def calibrateCavityAttenuator(Yoko,Acqiris,polarity = 1):
	Yoko.turnOn()
	voltages = arange(0.0,2.0,0.1)
	(ps,max,maxVoltage) = attenuatorRangeCheck(voltages,Yoko,Acqiris,polarity)
	voltages2 = arange(maxVoltage-0.1,maxVoltage+0.1,0.01)
	(p2s,max,maxVoltage2) = attenuatorRangeCheck(voltages2,Yoko,Acqiris,polarity)
	cla()
	plot(voltages2,p2s,voltages,ps)
	xlabel("attenuator voltage")
	ylabel("IQ variance")
	Yoko.setVoltage(maxVoltage2*polarity)
##
print "Adjusting rotation..."
adjustRotation(acqiris)
adjustRotation(acqiris2)
##

print "Calibrating setup 2"
calibrateCavityAttenuator(yoko2,acqiris2,polarity = 1)
print "Calibrating setup 1"
calibrateCavityAttenuator(yoko,acqiris,polarity = -1)

##
segments = 2000
points = 250
value = acqiris.AcquireV3(points = points,segments = segments,delay = 0)

print value[points:points+12]