# Provides the glue function, which makes stuff that comes in a serial port
#  go out a robust socket, and stuff coming in the socket goes out the
#  serial port.

import threading
import serial

# If nobody's listening on the serial port, writing will hang.
# In practice, we just want to throw out data if nobody's listening,
#  so we toss it if it takes more than some amount of time.
#  This number may have to change depending on the speed of the computer.
WRITE_TIMEOUT = 3 # Timeout in seconds

class SerialWrapper( serial.Serial ):
    """Thin wrapper around a Serial object to repurpose read and write."""
    def __init__( self, *args, **kwargs ):
        serial.Serial.__init__( self, *args, **kwargs )
        self.timeout = None
        self.writeTimeout = WRITE_TIMEOUT
    def read( self ):
        """Returns the next bunch of data to come in the serial port."""
        first = serial.Serial.read(self, 1)
        rest = serial.Serial.read(self, self.inWaiting())
        return first + rest
    def write( self, s ):
        """Writes data out the serial port. Discards it if it times out."""
        try:
            serial.Serial.write(self, s)
        except serial.serialutil.SerialTimeoutException:
            # If nobody's reading from the other end, we'll time out.
            # Whatever. Discard it.
            pass


class ReroutingThread( threading.Thread ):
    """Reads data from one stream and writes it into another."""
    def __init__( self, istream, ostream ):
        threading.Thread.__init__( self )
        self.istream = istream
        self.ostream = ostream
    
    def run( self ):
        while True:
            #print "Reading from", self.istream
            s = self.istream.read()
            #print "Writing to", self.ostream
            self.ostream.write( s )


def glue( options, sock, daemon=True ):
    """Glues a socket to a comm port with the given options."""
    ser = SerialWrapper( "\\\\.\\"+options.name, options.baud )
    ser_to_sock = ReroutingThread( ser, sock )
    sock_to_ser = ReroutingThread( sock, ser )
    ser_to_sock.daemon = daemon
    sock_to_ser.daemon = daemon
    ser_to_sock.start()
    sock_to_ser.start()
    
