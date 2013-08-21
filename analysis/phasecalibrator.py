from __future__ import absolute_import
from . import demodulation
from .datparsing import channels_labels, SAMPLES_PER_REVOLUTION, dat_dtype
from . import phaseplotter
import sys
import os
import ConfigParser
import numpy
import pickle

__doc__ = """Usage:
  phasecalculator.py FILENAME [n ...]
  phasecalculator.py -s FILENAME [n ...]
Finds the phase offsets to maximize each channel's mean Q or U value
in the given file. If the -s option is given, the file will be copied
to FILENAME_short.dat and truncated to the first hundred or so revolutions,
so the program will run faster. When the optimal phases are determined,
they're written to phases.cfg. Also, mean value as a function of phase is
plotted for the given chanel numbers (0-15)."""

def parse_command_line():
    args = sys.argv[1:]
    if args[0] == '-s':
        short = True
        args = args[1:]
    else:
        short = False
    fname, channelnums = args[0], map(int,args[1:])
    return short, fname, channelnums
    
def truncate( filename, revolutions=100 ):
    shortfilename = filename.replace('.dat', '_short.dat')
    m_in = numpy.memmap(filename, dtype=dat_dtype)
    first_data = m_in[:SAMPLES_PER_REVOLUTION*revolutions]
    m_out = numpy.memmap(shortfilename, dtype=dat_dtype,
                         mode='w+', shape=first_data.shape)
    m_out[:] = first_data[:]
    del m_in
    del m_out
    return shortfilename

def run( datfilename, channelnums, short=False ):
    if short:
        print "Truncating %s..."
        datfilename = truncate(datfilename)

    phases = ConfigParser.ConfigParser()
    channel_phase_info = dict(( (channel,{}) for channel in channels_labels ))

    for phase_offset in range(64):
        print "Updating phases.cfg..."
        for channel in channels_labels:
            phases.set('DEFAULT', channel, str(phase_offset))
        phases.write(open('phases.cfg','wb'))
        demodulation.update_phases()
        
        print "Demodulating with phase %d..." %phase_offset
        data = demodulation.demodulate_dat(datfilename)
            
        print "Finding mean Q for each channel..."
        for channel in channels_labels:
            mean = sum(data[channel+'Q']) / len(data[channel+'Q'])
            channel_phase_info[channel][phase_offset] = mean

    print "\nCompleted demodulation/averaging loop."
    for channel, phase_info in channel_phase_info.iteritems():
        best_phase, max_mean = max(phase_info.iteritems(), key=(lambda pm: pm[1]))
        print "Channel %s attained maximum %f at phase %d." %(channel,max_mean,best_phase)
        phases.set( 'DEFAULT', channel, str(best_phase) )
    phaseplotter.plot(channel_phase_info, channelnums)

if __name__ == '__main__':
    print "Running as main."
    short, fname, channelnums = parse_command_line()
    run(fname, channelnums, short=short)