import numpy

def write_dat( filename, data ):
    """Writes an array of data to disk."""
    m = numpy.memmap( filename, dtype=data.dtype, mode='w+',
                      shape=data.shape )
    m[:] = data[:]
    m.close()

def read_dat( filename, dtype ):
    """Reads a file on disk as an array of the given dtype."""
    return numpy.memmap( filename, dtype=dtype, mode='r' )