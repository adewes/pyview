MyManager = helpers.instrumentsmanager.Manager()
anritsu1 = MyManager.instrumentCopy("anritsu_mwg","anritsu1","GPIB0::4")
anritsu1 = MyManager.reloadInstrument("anritsu1","GPIB0::4")
anritsu2 = MyManager.instrumentCopy("anritsu_mwg","anritsu2","GPIB0::6")
anritsu2 = MyManager.reloadInstrument("anritsu2","GPIB0::6")
##
try:
	anritsu1.read()
	anritsu2.read()
except:
	pass
import time
while True:	
	try:
		print anritsu1.frequency()
	except:
		pass
	time.sleep(1)
##
anritsu1.setFrequency(7e9)
print anritsu1.frequency()
anritsu1.setPower(9)
print anritsu1.power()
anritsu1.turnOff()
anritsu2.turnOff()
##
print anritsu1.parameters()