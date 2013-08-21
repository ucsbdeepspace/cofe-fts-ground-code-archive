# This file contains tools for parsing the data contained in the .dat files
#  produced by the telescopes' data acquisition code.
# The most important things in this file are:
#  dat_dtype: the numpy dtype of the .dat files.
#  rev_dtype: the numpy dtype of a valid revolution's worth of data
#  read_raw(filename): a numpy.memmap of dtype=dat_dtype into the filename
#  iter_valid_revolutions(raw): generates length-1 arrays of rev_dtype,
#    representing the data gathered during valid revolutions of the
#    polarization disk.
# We recognize when a new revolution starts by seeing that the encoder
#  value is less than ENCODER_START_TRIGGER.
# A "valid" revolution is one with exactly SAMPLES_PER_REVOLUTION samples.
#  Any other is damaged in some way, and recommended to be ignored.

import numpy

SAMPLES_PER_REVOLUTION = 256
NUM_DATA_CHANNELS = 16
ENCODER_START_TRIGGER = 16

# Names of the data channels:
channels_labels = ['Channel_%02d' % i for i in range(NUM_DATA_CHANNELS)]

# Structure of the data we read from the .dat files:
dat_dtype = numpy.dtype( [(ch,numpy.uint16) for ch in channels_labels] +\
                         [('enc',numpy.uint16)]+[('dummy',numpy.uint16)]  +\
                         [('rev%d' % i,numpy.uint16) for i in range(3)])
# Structure of the data representing a single valid revolution:
rev_dtype = numpy.dtype( [('rev',numpy.long)] +\
                         [(ch,numpy.float,SAMPLES_PER_REVOLUTION)
                          for ch in channels_labels] )

def read_raw( filename ):
    return numpy.memmap(filename,dtype=dat_dtype,mode='r')

def valid_raw_to_revs( valid_raw ):
    rev_starts = valid_raw[::SAMPLES_PER_REVOLUTION]
    result = numpy.zeros( len(rev_starts), dtype=rev_dtype )
    result['rev'] = rev_starts['rev0'].astype(numpy.long) +\
                    rev_starts['rev1'].astype(numpy.long) * SAMPLES_PER_REVOLUTION +\
                    rev_starts['rev2'].astype(numpy.long) * SAMPLES_PER_REVOLUTION**2
    for ch in channels_labels:
        voltages = valid_raw[ch] * 20./2**16 - 10
        result[ch] = voltages.reshape((-1, SAMPLES_PER_REVOLUTION))
    return result

def iter_valid_rev_start_indices( raw ):
    enc = raw['enc']
    start = 0
    
    while start < len(raw):
        window = enc[start : start+SAMPLES_PER_REVOLUTION]
        if len(window) < SAMPLES_PER_REVOLUTION:
            break
        window_rev_starts, = numpy.where(window < ENCODER_START_TRIGGER)
        if (len(window_rev_starts) == 1) and (window_rev_starts[0] == 0):
            yield start
            start += SAMPLES_PER_REVOLUTION
        elif len(window_rev_starts) > 0:
            start += window_rev_starts[-1]
        else:
            start += SAMPLES_PER_REVOLUTION

def count_valid_revolutions( raw ):
    result = 0
    for i in iter_valid_rev_start_indices(raw):
        result += 1
    return result

def iter_valid_revolutions( raw ):
    for i in iter_valid_rev_start_indices(raw):
        window = raw[i : i+SAMPLES_PER_REVOLUTION]
        yield valid_raw_to_revs(window)

def iter_chunks( raw, size=20 ):
    window_size = size*SAMPLES_PER_REVOLUTION
    enc = raw['enc']
    start = 0
    print "Intended window size:", window_size
    while start < len(raw):
        window = numpy.array(raw[start:start+window_size])
        window_rev_starts, = numpy.where(window['enc'] < ENCODER_START_TRIGGER)
        boundaries = [0]+list(window_rev_starts)+[len(window)]
        boundaries.reverse()
        for i in range(len(boundaries)-1):
            b1,b2 = boundaries[i+1], boundaries[i]
            if b2-b1 != SAMPLES_PER_REVOLUTION:
                window = numpy.delete(window, numpy.s_[b1:b2])
        if len(window) > 0:
            yield window
        if (len(window_rev_starts) > 0) and (window_rev_starts[0] > 0):
            start += window_rev_starts[-1]
        else:
            start += window_size
