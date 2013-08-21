# Provides headering capability for streams.
# The HeaderedStream class allows the user to read and write data
#  in discrete chunks. The point is to prevent problems like:
#   The telescope computer is sending data to the flight computer
#    in 49-byte chunks. The ethernet monster eats byte #49 in one
#    message.
#   Without headering: what the flight computer reads is offset
#    by 1. Forever after, what the flight computer thinks is byte
#    #4 is actually byte #5, what it thinks is #5 is actually #6,
#    and so on. Every field is wrong. Forever.
#   With headering: the first byte of the header of the following
#    message is interpreted as byte #49 in the damaged message.
#    The checksum for the damaged message isn't right anymore,
#    so it's discarded. The header for the next message is also
#    trashed now, since the first byte is missing, so we miss the
#    next message too. After that, though, everybody's still
#    synced up.
#
# And that's good. Of course, if the 49-byte chunks were part
#  of a larger structure, we'd be missing two pieces. But fixing
#  that would get us into the realm of packet sequencing, and
#  that's a lot of work, and this seems to be sufficient for
#  the needs of COFE.
#
# A header is a string of a fixed length that looks like:
# <identifying string> + <meta (digits)> + <size (digits)>
#  + <header checksum (digits)> + <message checksum (digits)>
# Although currently, the meta field is not used.
#  Or completely implemented, really.
# The header checksum incorporates the meta and length of the string,
#  guarding us against changes to either of those, and the message checksum
#  incorporates the beginning and end of the string (currently the first and
#  last 10 characters), guarding against byte insertion or deletion (though not
#  substitution -- I think that's less important, and I don't want to have to
#  write a fast, version-independent hash function for strings).
#
# The punch line of this file is the HeaderedStream class.
#  Assume you have a function read_stream which takes an integer N and returns
#   a string no more than N bytes long, and a function write_stream which takes
#   a string.
#  HeaderedStream( read_stream, write_stream ) returns an object
#  with two important methods:
#   hs.write(s) calculates the header for the given string, and passes
#    header+s to write_stream (call that string a "packet", with a header
#    and some contents).
#   hs.read() returns the contents of the next packet received.
#    It will ignore "garbage" read from read_stream, i.e. data sent
#    when the HeaderedStream is expecting a header.
#
# Example:
#  hs = HeaderedStream( read_function, write_function )
#  hs.write( "It is a truth universally acknowledged" )# will pass
#   # "Header!00000000003882186772It is a truth universally acknowledged"
#   # to write_function (if the header checksum of meta=0,
#   #  size=len("It is...")=38 is 8218 and the message checksum of
#   #  "It is..." is 6772).
#  hs.write( " that a single man in possession" )
#  write_function( "GARBAGE GARBAGE BLAH BLAH BLAH" )
#  hs.write( " of a good fortune, must be" )
#  write_function( header(" in want of a wife.") + " inwant of a wife." )
#  hs.write( "\n\nHowever little known" )
#  hs.write( " the feelings or views" )
#  write_function( header(" of such a man") + "~ of such a man" )
#  hs.write( " may be on his first entering" )
#
#  Now, assume read_function is hooked directly up to write_function,
#   so bytes passed to write_function will be queued up, and
#   read_function dequeues them (or blocks until the queue is nonempty).
#   Then,
#  hs.read()# => "It is a truth universally acknowledged"
#  hs.read()# => " that a single man in possession"
#  hs.read()# => " of a good fortune, must be"
#   # Note that the "GARBAGE" string was completely ignored.
#  hs.read()# => " the feelings or views"
#   # Because " in want of a wife." got shortened, part of the header
#   # for the next message was read at the end. This ruined the checksum
#   # of the " in want of a wife." packet, so it was discarded.
#   # It also trashed the header of the next packet, so everything was
#   # ignored until a valid header, which came right before
#   # " the feelings or views".
#  hs.read()# => " may be on his first entering"
#   # The extra character in "~ of such a man" ruined the checksum for
#   # that packet, but since we have an EXTRA byte instead of a missing
#   # one, we just see a byte of garbage before the next header
#   # (which is for " may be on...").
#  hs.read()
#   # This will hang indefinitely, until another complete, valid packet
#   # is written to write_function.

IDENTIFYING_STRING = 'Header!'
NUM_META_CHARS = 2
NUM_SIZE_CHARS = 10
NUM_HCHECKSUM_CHARS = 4
NUM_MCHECKSUM_CHARS = 4
# So a header looks like "Header!0400000054512345678"
# where the "meta" is 4, the number of bytes of meaningful data that follow
# is 545, the checksum of the meta and size is 1234, and the checksum of
# the data is 5678.

HEADER_SIZE = len(IDENTIFYING_STRING) + NUM_META_CHARS +\
              NUM_SIZE_CHARS + NUM_HCHECKSUM_CHARS +\
              NUM_MCHECKSUM_CHARS

META_FORMAT_STRING = '%0' + str(NUM_META_CHARS) + 'd'
SIZE_FORMAT_STRING = '%0' + str(NUM_SIZE_CHARS) + 'd'
HCHECKSUM_FORMAT_STRING = '%0' + str(NUM_HCHECKSUM_CHARS) + 'd'
MCHECKSUM_FORMAT_STRING = '%0' + str(NUM_MCHECKSUM_CHARS) + 'd'

def header( s, meta=0 ):
    """Generates the header for a message."""
    if (not isinstance(meta,int)) or (not 0<=meta<100):
        raise ValueError( "meta of a message must be a two-digit integer" )
    size = len(s)
    if size >= 10**NUM_SIZE_CHARS:
        raise ValueError( ''.join(("This file was written back when a ",
                                   "10**%d-byte " %NUM_SIZE_CHARS,
                                   "message was ridiculously large. ",
                                   "Sorry, kids. Love, Grandpa.")) )
    meta_str = META_FORMAT_STRING %meta
    size_str = SIZE_FORMAT_STRING %size
    hchecksum = HCHECKSUM_FORMAT_STRING % generate_header_checksum( meta, size )
    mchecksum = MCHECKSUM_FORMAT_STRING % generate_message_checksum( s )
    return IDENTIFYING_STRING + meta_str + size_str + hchecksum + mchecksum
    
def generate_header_checksum( meta, size ):
    """Calculates the checksum for a given string and meta."""
    # I'd LIKE to use the hash function, but the result varies from
    #  version to version of Python, so I'll just hard-code it here.
    # Just gonna multiply each hash by a big prime and add them together.
    result = meta*9733 + size*8111
    result %= 10**NUM_HCHECKSUM_CHARS
    return result
def generate_message_checksum( s ):
    """Returns a hash dependent on the first and last several characters of a string."""
    primes = [8599,8933,5839,6359,7207,11027,823,1283,2713,2909]
    result = 0
    for i in range(min(len(primes),len(s))):
        result += primes[i] * ord(s[i])
        result += primes[i] * ord(s[-1-i])
    result %= 10**NUM_MCHECKSUM_CHARS
    return result

def is_valid_header( h ):
    """Returns whether a header's shape and checksum is valid."""
    if len(h) != HEADER_SIZE:
        return False
    if not h.startswith(IDENTIFYING_STRING):
        return False
    h = h[len(IDENTIFYING_STRING):]
    try:
        meta, h = int(h[:NUM_META_CHARS]), h[NUM_META_CHARS:]
        size, h = int(h[:NUM_SIZE_CHARS]), h[NUM_SIZE_CHARS:]
        hchecksum = int(h[:NUM_HCHECKSUM_CHARS])
    except ValueError:
        return False
    return generate_header_checksum(meta,size) == hchecksum

def parse_header( h ):
    """Parses a valid header, returns (meta, size, hchecksum, mchecksum)."""
    if not is_valid_header(h):
        raise ValueError( "trying to parse invalid header" )
    h = h[len(IDENTIFYING_STRING):]
    meta, h = int(h[:NUM_META_CHARS]), h[NUM_META_CHARS:]
    size, h = int(h[:NUM_SIZE_CHARS]), h[NUM_SIZE_CHARS:]
    hchecksum, h = int(h[:NUM_HCHECKSUM_CHARS]), h[NUM_HCHECKSUM_CHARS:]
    mchecksum = int(h)
    return meta, size, hchecksum, mchecksum


class HeaderedStream( object ):
    READ_SIZE = 4096
    def __init__( self, read_function, write_function ):
        self.read_function = read_function
            # Takes an integer argument, returns a string of up to that length.
            # The input stream.
        self.write_function = write_function
            # Takes a string. The output stream.

        self.recv_buffer = ''
            # The buffer for data that we've read from read_function
            #  but not processed yet. Generated by read_until_header
            #  and consumed by read_chars.
        
    def read( self ):
        """Returns next valid data packet in queue, or next received."""
        while True:
            self.read_until_header()
            h = self.read_chars(HEADER_SIZE, exact=True)
            try:
                meta, size, hchecksum, mchecksum = parse_header(h)
            except ValueError:
                # For robustness for COFE, I'll catch this error.
                # In any other application, I'd take out this try/except.
                continue
            result = self.read_chars(size, exact=True)
            if generate_message_checksum( result ) == mchecksum:
                #print "Read %s" %result
                print "Read %d chars." %len(result)
                return result, meta
        
    def write( self, data, meta=0 ):
        """Writes the string data using the given function."""
        self.write_function( header(data,meta=meta) + data )
        #print "Wrote %s" %data
        print "Wrote %d chars." %len(data)
    
    def read_until_header( self ):
        """Reads from the given function until a header is reached, puts header and some following data in recv_buffer"""
        i = self.find_header_in_buffer()
        while i == -1:
            self.recv_buffer = self.recv_buffer[-HEADER_SIZE:]
            self.recv_buffer += self.read_chars(self.READ_SIZE)
            i = self.find_header_in_buffer()
        self.recv_buffer = self.recv_buffer[i:]
        
    def find_header_in_buffer( self ):
        """Returns starting index of first valid header in recv_buffer, or -1 if none is found."""
        i = self.recv_buffer.find(IDENTIFYING_STRING)
        while i != -1:
            if is_valid_header( self.recv_buffer[i:i+HEADER_SIZE] ):
                return i
            i = self.recv_buffer.find(IDENTIFYING_STRING,i+1)
        return i
            
    def read_chars( self, maxsize, exact=False ):
        """Returns up to n bytes from the input stream (exactly n if exact is True)."""
        minsize = (maxsize if exact else 1)
        result, self.recv_buffer = self.recv_buffer[:maxsize], self.recv_buffer[maxsize:]
        while len(result) < minsize:
            result += self.read_function(maxsize-len(result))
        assert minsize <= len(result) <= maxsize
        return result


if __name__ == '__main__':
    # Test the program by sending the lines of Pride and Prejudice one-by-one.
    f = open('prideandprejudice.txt')
    # Filter out blank lines. Just 'cause.
    lines = (line for line in f.readlines() if (line.strip() != ''))
    f.close()
    
    global source
    source = ''.join((header(line)+line for line in lines))
    
    def emulate_read( size ):
        global source
        result, source = source[:size], source[size:]
        return result
    
    istream = HeaderedStream( emulate_read, None )
    for line in lines:
        s = istream.read()
        if s != line:
            print "s = %s\n should be %s" %(s,line)
            exit()
    else:
        print "All lines match. Awesome."
    
    
    source = ''
    def write_function( data ):
        global source
        source += data
    def read_function( n ):
        global source
        if source == '':
            print "Source is empty."
            exit()
        result,source = source[:n], source[n:]
        return result

    hs = HeaderedStream( read_function, write_function )
    hs.write( "It is a truth universally acknowledged" )
    hs.write( " that a single man in possession" )
    write_function( "GARBAGE GARBAGE BLAH BLAH BLAH" )
    hs.write( " of a good fortune, must be" )
    write_function( header(" in want of a wife.") + " inwant of a wife." )
    hs.write( "\n\nHowever little known" )
    hs.write( " the feelings or views" )
    write_function( header(" of such a man") + "~ of such a man" )
    hs.write( " may be on his first entering" )

    print "The source should not be empty until..."
    tmp = hs.read()
    #print tmp
    assert tmp[0] == "It is a truth universally acknowledged", tmp
    tmp = hs.read()
    #print tmp
    assert tmp[0] == " that a single man in possession", tmp
    tmp = hs.read()
    #print tmp
    assert tmp[0] == " of a good fortune, must be", tmp
    tmp = hs.read()
    #print tmp
    assert tmp[0] == " the feelings or views"
    tmp = hs.read()
    #print tmp
    assert tmp[0] == " may be on his first entering"

    print "...now."
    tmp = hs.read()
    print "Last read (should have exited):", tmp
