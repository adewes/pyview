MyManager = helpers.instrumentsmanager.Manager()
agilent1 = MyManager.instrumentCopy("agilent_mwg","agilent1","TCPIP0::192.168.0.13::inst0")
MyManager.reloadInstrument("agilent1")
anritsu1 = MyManager.instrumentCopy("anritsu_mwg","anritsu1","GPIB0::4")
MyManager.reloadInstrument("anritsu1")
anritsu2 = MyManager.instrumentCopy("anritsu_mwg","anritsu2","GPIB0::6")
MyManager.reloadInstrument("anritsu2")
acqiris = MyManager.instrument("acqiris_client")
yoko = MyManager.instrument("yokogawa")
vna = MyManager.instrument("vna","GPIB0::15")
vna = MyManager.reloadInstrument("vna")
vna2 = MyManager.instrumentCopy("vna","vna2","GPIB0::16")
vna2 = MyManager.reloadInstrument("vna2")
tempSensor = MyManager.instrument("temperature")
tempSensor = MyManager.reloadInstrument("temperature")
print "Done"
print vna
##
print temp.temperature()
##
print "Starting"
import time
import visa
print "Asking..."
anritsu1.write("*IDN?")
print "Done"
##
data = zeros((0,7))
cnt = 0
os.chdir("L:\\local-expdata\\B4-2ndRun")
globalIndex = 1
print "Starting..."
while True:
	try:
		vna.waitFullSweep()
		l1 = vna.electricalLength()
		l2 = vna2.electricalLength()
		(freqs1,mag1,phase1) = vna.getTrace()
		(freqs2,mag2,phase2) = vna2.getTrace()
		vals1 = zeros((len(freqs1),3))
		vals1[:,0] = freqs1
		vals1[:,1] = mag1
		vals1[:,2] = phase1
		savetxt("vna1-%d_%d.txt" % (globalIndex,cnt),vals1)		

		vals2 = zeros((len(freqs2),3))
		vals2[:,0] = freqs2
		vals2[:,1] = mag2
		vals2[:,2] = phase2
		savetxt("vna2-%d_%d.txt" % (globalIndex,cnt),vals2)		

		temp = tempSensor.temperature()
		t = time.time()
		data = resize(data,(cnt+1,7))
		data[cnt,0]=cnt
		data[cnt,1]=t 
		data[cnt,2]=temp
		data[cnt,3]=l1
		data[cnt,4]=l2 
		data[cnt,5]=mag1[len(mag1)/2]
		data[cnt,6]=mag2[len(mag2)/2]
		print "%d, T: %f, L1: %f, L2: %f, M1: %f, M2: %f" % (cnt,temp,l1,l2,mag1[len(mag1)/2],mag2[len(mag2)/2])
		savetxt("cooldown-electrical-length-%d.txt" % globalIndex,data)
		cnt+=1
	except SystemExit:
		print "Exiting..."
		exit(0)
	except:
		print "An error occured. Continuing anyway..."	
		print sys.exc_info()
	print "..."
##

##
params = MyManager.parameters()
print params
import yaml
text =  yaml.dump(params, default_flow_style=False)
print text
newParams = yaml.load(text)
print newParams