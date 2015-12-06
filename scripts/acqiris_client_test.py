import socket
import sys
import struct

HOST, PORT = "localhost", 2200
data = "AcquireV2|15|1000|250|11|1|0.000000|\0"
params = [2,250,2,250,180,0,0,0,0,0]
for param in params:
	data+=struct.pack("d",double(param))
data+='\0'
print "\"{0!s}\"".format(data)
print "Length: {0:d}".format(len(data))
##
# SOCK_DGRAM is the socket type to use for UDP sockets
for i in range(0,1):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(10)
	sock.connect((HOST, PORT))

	print "Sent:"+str(sock.send(data))

	chunk = 2048
	buffer = ""
	received = sock.recv(chunk)
	while len(received)>0:	
		buffer+=received
		received = sock.recv(chunk)

	print "Sent:     {0!s}".format(data)
	strlen = 0
	print "Done"
	print type(buffer)
	print "Buffer length: {0:d}".format(len(buffer))
	for i in range(0,len(buffer)):
		code = struct.unpack("B1",buffer[i])[0]
		if code == 0:
			print "Found zero!"
			strlen = i 
			break
	print "Length: {0:d}".format(strlen)
	print len(buffer)
	print buffer[0:strlen]
	index0 = strlen
	string = ""
	fieldLen = 8
	values = []
	for i in range(0,(len(buffer)-index0)/fieldLen):
		values.append(struct.unpack("d",buffer[index0+i*fieldLen:index0+(i+1)*fieldLen])[0])
	print index0
##
figure(1)
cla()
print "Received {0:d} points".format(len(values))
scatter(range(0,len(values)),values)
figure(2)
cla()
scatter(values[1000:2000],values[3000:4000])
