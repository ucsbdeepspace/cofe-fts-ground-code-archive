import sys
import robustsocket
import time
import random

port1 = 5007
port2 = 5008

def garbage(n):
    """Returns n characters."""
    return '.'*n
    
server = (sys.argv[1] == 'server')
if server:
    s = robustsocket.RobustSocket(port1, None)
else:
    s = robustsocket.RobustSocket(port2, ('127.0.0.1',port1))
    s.connect()

if server:
    while True:
#        print "Writing garbage."
        for i in range(10):
            s.write(garbage(2**13))
        print time.time()
        time.sleep(.2)
else:
    while True:
#        print "Entering read loop."
        s.read()
        print time.time()
#        time.sleep(.011)
