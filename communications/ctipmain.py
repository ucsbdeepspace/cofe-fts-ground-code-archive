# This file is intended to be run as a script, rather than included.
# It provides a command-line tool to glue a socket and a serial port together,
#  so that data that goes into one comes out the other.
# Usage:
#  python ctipmain.py [options]
# Options:
#  -a ADDR: the IP address of the server to connect to.
#           If unspecified, you are the server.
#  -p PORT: the port to connect to, if client, or listen on, if server.
#  -n NAME: the name (excluding '\\.\') of the comm port to glue to.
#  -b BAUD: the baud rate for the comm port.
#  -l: turns on logging, where everything coming in or going out through
#      the socket is copied into a file. Off by default.
#

import optparse
import ctipglue
import serial
from robustness import robustsocket

DEFAULT_PORT = 4578
DEFAULT_NAME = "COMIP"
DEFAULT_BAUD = 9600

# Add command-line options.
parser = optparse.OptionParser()
parser.add_option( "-p", "--port", action="store",
                   type="int", dest="port", default=DEFAULT_PORT,
                   help="the port to listen on/look for" )
parser.add_option( "-a", "--address", action="store",
                   type="str", dest="address", default=None,
                   help="the IP address of the host (client-only)" )
parser.add_option( "-n", "--name", action="store",
                   type="str", dest="name", default=DEFAULT_NAME,
                   help="the name of the serial port to glue to" )
parser.add_option( "-b", "--baud", action="store",
                   type="int", dest="baud", default=DEFAULT_BAUD,
                   help="the baud rate of the connection" )

def run( options, daemon=True ):
    """Connects the socket and starts streaming between it and the comm port."""
    print "Serial port name:", options.name
    print "Baud:", options.baud
    if options.address:
        sock = robustsocket.RobustSocket( port=0, peer=(options.address,options.port) )
        sock.connect()
    else:
        sock = robustsocket.RobustSocket( port=options.port, peer=None )
    # Now glue the serial port and socket together.
    ctipglue.glue( options, sock, daemon=daemon )



if __name__ == '__main__':
    options, _args = parser.parse_args()
    run(options, daemon=False)
