import socket
import random

class HandshakeFailure( Exception ):
    pass

class StartupHandshake( object ):
    VALIDITY_STR = '_!VALID!_'
    N_RAND_CHARS = 5
    START_LEN = len(VALIDITY_STR) + N_RAND_CHARS
    def execute_server( self, sock ):
        v = self.VALIDITY_STR +  ''.join([chr(random.randrange(256))
                                          for i in range(self.N_RAND_CHARS)])
        print "Validity str is {0!r}".format(v)
        sock.send(v)
        if sock.recv(len(v)) != v:
            raise HandshakeFailure
    def execute_client( self, sock ):
        start = sock.recv(self.START_LEN)
        if start.startswith(self.VALIDITY_STR):
            sock.send(start)
        else:
            raise HandshakeFailure

class PortAgreementHandshake( object ):
    N_CHARS = 5
    def execute_server( self, sock, port ):
        sock.send("{port:{width}d}".format(port=port, width=self.N_CHARS))
        try:
            return int(sock.recv(self.N_CHARS))
        except ValueError:
            raise HandshakeFailure
    def execute_client( self, sock, port ):
        try:
            result = int(sock.recv(self.N_CHARS))
        except ValueError:
            raise HandshakeFailure
        sock.send("{port:{width}d}".format(port=port, width=self.N_CHARS))
        return result
        
        
# FOR ROBUSTSOCKETV2
class Handshake(object):
    pass

_VALSTR = '_!VALID!_'
_N_RAND = 5
startup = Handshake()
def _startup_server(sock):
    v = _VALSTR + ''.join([chr(random.randrange(256))
                           for i in range(_N_RAND)])
    sock.send(v)
    return (sock.recv(len(v)) == v)
def _startup_client(sock):
    start = sock.recv(len(_VALSTR)+_N_RAND)
    if start.startswith(_VALSTR):
        sock.send(start)
        return True
    return False

startup.server = _startup_server
startup.client = _startup_client

_N_PORT = 5
port_agreement = Handshake()
def _pa_server(sock, port):
    sock.send(_VALSTR + "{port:{width}d}".format(port=port, width=_N_PORT))
    try:
        val = sock.recv(len(_VALSTR))
        if val != _VALSTR:
            print "Invalid verification: {0}".format(val)
            raise socket.error
        return int(sock.recv(_N_PORT))
    except ValueError:
        print "Invalid port value."
        raise socket.error
def _pa_client(sock, port):
    try:
        val = sock.recv(len(_VALSTR))
        if val != _VALSTR:
            print "Invalid verification: {0}".format(val)
            raise socket.error
        result = int(sock.recv(_N_PORT))
    except ValueError:
        print "Invalid port value."
        raise socket.error
    sock.send(_VALSTR + "{port:{width}d}".format(port=port, width=_N_PORT))
    return result

port_agreement.server = _pa_server
port_agreement.client = _pa_client
