import time
import threading
import socket
from headers import HeaderedStream
import handshakes

STD_INTERVAL = 2

class RunForeverThread( threading.Thread ):
    def __init__( self, callback ):
        self.callback = callback
        threading.Thread.__init__( self )
    def run(self):
        while True:
            self.callback()

class StateLock( object ):
    class _ContextHandler( object ):
        def __init__( self, state_lock, state ):
            self._state_lock = state_lock
            self._state = state
        def __enter__( self ):
            return self._state_lock.acquire(self._state)
        def __exit__( self, *args ):
            self._state_lock.release()
            
    def __init__( self, states ):
        self.contexts = dict(((s,self._ContextHandler(self,s))
                              for s in states))
        
        self._state = None
        self._states = states
        self._users = dict(((s,0) for s in states))
        
        lock = threading.Lock()
        self._conds = dict(((s,threading.Condition(lock)) for s in states))
    
    @property
    def _open( self ):
        return (sum(self._users.values()) == 0)

    def acquire( self, state, blocking=True ):
        with self._conds[state]:
            if self._open or (state == self._state):
                self._users[state] += 1
                self._state = state
                return True
            elif blocking:
                self._users[state] += 1
                self._conds[state].wait()
                return True
            else:
                return False

    def release( self ):
        with self._conds[self._state]:
            self._users[self._state] -= 1
            if self._users[self._state] == 0:
                for state in self._states:
                    if self._users[state] > 0:
                        self._state = state
                        self._conds[state].notify_all()
                        break
    
    def wait( self, state, timeout=None ):
        with self._conds[state]:
            if self._open or (state == self._state):
                return
            else:
                self._conds[state].wait(timeout)

class RobustSocket( HeaderedStream ):
    def __init__( self, port, peer ):
        self.accepter = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.accepter.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.accepter.bind(('', port))
        self.accepter.listen(1)
        self.conn = None
        
        self.port = self.accepter.getsockname()[1]
        self.peer = peer
        RunForeverThread(self.accept).start()
        
        self.state = StateLock(['connected','disconnected'])
        self.connected = threading.Event()
        self.connected.clear()
        
        HeaderedStream.__init__( self, self.read_from_socket, self.write_to_socket )
    
    def read( self ):
        return HeaderedStream.read(self)[0]
    
    def read_from_socket( self, maxsize ):
        while True:
            try:
                self.connected.wait()
                with self.state.contexts['connected']:
                    result = self.conn.recv(maxsize)
                if not result:
                    raise socket.error
                return result
            except socket.timeout:
                print "Timed out while reading."
                pass
            except socket.error as e:
                print "Error reading: {0}".format(e)
                self.reconnect()
    
    def write_to_socket( self, data ):
        while True:
            try:
                self.connected.wait()
                with self.state.contexts['connected']:
                    self.conn.send(data)
                    print "Wrote {0} chars.".format(len(data))
                    return
            except socket.timeout:
                print "Timed out while writing."
                time.sleep(STD_INTERVAL)
            except socket.error as e:
                print "Error writing: {0}".format(e)
                self.reconnect()
    
    def accept( self ):
        print "Listening for connection on {0}...".format(self.accepter.getsockname()[1])
        conn,addr = self.accepter.accept()
        print "Got one!"
        conn.settimeout(STD_INTERVAL)
        try:
            self.peer = (addr[0], handshakes.port_agreement.server(conn,self.port))
        except socket.error:
            print "Received bad connection."
        else:
            print 'Received connection from {0}'.format(addr)
            self.conn, self.peer = conn, (addr[0],self.peer[1])
            self.connected.set()
    def connect( self ):
        while True:
            try:
                self.conn = socket.create_connection(self.peer)
                self.conn.settimeout(STD_INTERVAL)
                handshakes.port_agreement.client(self.conn, self.port)
            except socket.error as e:
                print "Error connecting: {0}".format(e)
                time.sleep(STD_INTERVAL)
            else:
                print 'Successfully connected as {0}'.format(self.conn.getsockname())
                self.connected.set()
                return

    def disconnect( self ):
        self.connected.clear()
        self.conn.close()
    def reconnect( self ):
        if self.state.acquire('disconnected',False):
            print 'Reconnecting'
            try:
                self.disconnect()
                self.connect()
            finally:
                self.state.release()
        else:
            print 'Waiting for reconnect to finish'
            self.state.wait('connected')


if __name__ == '__main__':
    # I hope you like testing! 'Cause we're gonna be doing some!
    #
    # Here is a list of all events we want to test.
    #  Connection initialization
    #  Server starts reading, then client writes.
    #  Client starts reading, then server writes.
    #  Client vanishes while server is idle.
    #    ...and the server tries to read before it realizes the client is missing.
    #    ...and the server tries to write before it realizes the client is missing.
    #  Server vanishes while client is idle.
    #    ...and the client tries to read before it realizes the server is missing.
    #    ...and the client tries to write before it realizes the server is missing.
    #  Client vanishes while server is reading.
    #  Server vanishes while client is reading.
    #  Client vanishes and quickly reappears.
    #  ...
    DELIMITER = 50 * "#"
    s = RobustSocket(4578, (None,4579))
    c = RobustSocket(4579, ('127.0.0.1',4578))
    
    print DELIMITER
    print "Testing: connection initialization."
    time.sleep(2)
    c.connect()
    print "Connected"
    #c.write_to_socket("Hi")
    #print s.read_from_socket(2)
    c.write("Hi.")
    print "Wrote (c)"
    read = s.read()
    print "Read: {0}".format(read)
    assert read == "Hi."
    s.write("Hello!")
    print "Wrote (s)"
    assert c.read() == "Hello!"
    print "Passed."
    
    print DELIMITER
    print "Testing: Server starts reading, then client writes."
    threading.Timer(2, (lambda: c.write("Late."))).start()
    assert s.read() == "Late."
    print "Passed."
    
    print DELIMITER
    print "Testing: Client starts reading, then server writes."
    threading.Timer(2, (lambda: s.write("Me too."))).start()
    assert c.read() == "Me too."
    print "Passed."
    
    print DELIMITER
    print "Testing: Client vanishes while server is idle."
    c.disconnect()
    time.sleep(2*STD_INTERVAL)
    c.connect()
    c.write("I'm back!")
    assert s.read() == "I'm back!"
    s.write("Awesome.")
    assert c.read() == "Awesome."
    print "Passed."
    
    print DELIMITER
    print "What if the server tries to read before the client comes back?"
    c.disconnect()
    def _f():
        print "  A"
        c.connect()
        print "  B"
        c.write("Again")
        print "  C"
    threading.Timer(3*STD_INTERVAL, _f).start()
    assert s.read() == "Again"
    print "Passed."
    
    print DELIMITER
    print "What if the server tries to write before the client comes back?"
    c.disconnect()
    s.write("First message.")
    threading.Timer(3*STD_INTERVAL, (lambda: s.write("Second message."))).start()
    c.connect()
    print "  A"
    time.sleep(2*STD_INTERVAL)
    print "  B"
    result = c.read()
    print "  C"
    assert (result=="First message.") or (result=="Second message.")
    print "Passed."
    if result == "Second message.":
        print " (The first message got eaten, though.)"
    else:
        print " (And the first message got through.)"
        c.read()
    
    print DELIMITER
    print "Testing: Server vanishes while client is idle."
    s.disconnect()
    time.sleep(2*STD_INTERVAL)
    s.connect()
    s.write("I'm back!")
    assert c.read() == "I'm back!"
    c.write("Awesome.")
    assert s.read() == "Awesome."
    time.sleep(2*STD_INTERVAL)
    print "Passed."
    
    print DELIMITER
    print "What if the client tries to read before the server comes back?"
    s.disconnect()
    threading.Timer(2*STD_INTERVAL,(lambda: (s.connect(),s.write("Again")))).start()
    assert c.read() == "Again"
    time.sleep(2*STD_INTERVAL)
    print "Passed."
    
    print DELIMITER
    print "What if the client tries to write before the server comes back?"
    s.disconnect()
    c.write("First message.")
    threading.Timer(3*STD_INTERVAL, (lambda: c.write("Second message."))).start()
    s.connect()
    time.sleep(2*STD_INTERVAL)
    result = s.read()
    assert (result=="First message.") or (result=="Second message.")
    print "Passed."
    if result == "Second message.":
        print " (The first message got eaten, though.)"
    else:
        print " (And the first message got through.)"
        s.read()
    
    print DELIMITER
    print "Testing: Client vanishes while server is reading."
    t = threading.Thread(target=s.read)
    t.start()
    c.disconnect()
    time.sleep(2*STD_INTERVAL)
    c.connect()
    c.write("Hi.")
    t.join()
    c.write("Hi again.")
    result = s.read()
    assert (result=="Hi.") or (result=="Hi again.")
    time.sleep(2*STD_INTERVAL)
    print "Passed."
    if result == "Hi again.":
        print " (The first message got eaten, though.)"
    else:
        print " (And the first message got through.)"
        s.read()
    
    print DELIMITER
    print "Testing: Server vanishes while client is reading."
    t = threading.Thread(target=c.read)
    t.start()
    s.disconnect()
    time.sleep(2*STD_INTERVAL)
    s.connect()
    s.write("Hi.")
    t.join()
    s.write("Hi again.")
    result = c.read()
    assert (result=="Hi.") or (result=="Hi again.")
    time.sleep(2*STD_INTERVAL)
    print "Passed."
    if result == "Hi again.":
        print " (The first message got eaten, though.)"
    else:
        print " (And the first message got through.)"
        c.read()
    
    print DELIMITER
    print "Testing: Client vanishes and quickly reappears."
    c.disconnect()
    c.connect()
    s.write("Welcome back.")
    assert c.read() == "Welcome back."
    print "Passed."    
    
    
    time.sleep(.1)
    s.disconnect()
    c.disconnect()
