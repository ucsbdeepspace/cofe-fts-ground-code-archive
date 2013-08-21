# This file provides functions to perform the demodulation of the
#  telescopes' .dat files.
# The important functions here are:
#  update_phases(): updates the phase offsets used in demodulation,
#    using the information in phases.cfg. Called automatically upon
#    loading the module, and must be called manually any time you want
#    to update it.
#  demodulate(data): demodulates the given data (assumed to be in the
#    format read from the telescopes' .dat files).
#  demodulate_dat(filename): reads the data in the given .dat file and
#    demodulates it into an array of data type demod_dtype.
#
# Here is a lengthy explanation of what the demodulation process is and
#  why we do it that way:
# Okay. So, we have this thing called a half-wave plate, which is a metal
#  plate with a bunch of parallel wires across the front. Its effect is
#  this: light comes in. Part of it is unpolarized, and that is reflected
#  off the plate normally. Part of it is completely polarized, and the
#  direction of polarization is mirrored around the plane (a) perpendicular
#  to the disk and (b) including the wire where the light is hitting.
# Because of how mirroring works, this means that the direction of the
#  polarization we're measuring rotates twice for every time the half-wave
#  plate rotates. On top of that, since light polarized "leftwards"
#  is the same as light polarized "rightwards", we get four cycles of
#  up-down-ness to left-right-ness.
# Now, from that information, we want to calculate two numbers, Q and U.
#  Q is (vertical polarization) minus (horizontal polarization),
#  so in one revolution it goes (high,low,high,low,high,low,high,low):
#  one (high,low) for each time the measured polarization direction
#  goes from vertical to horizontal.
#  U is (up-rightish polarization) minus (down-rightish polarization),
#  so it's KIND OF like Q phase-shifted forward by half a (high,low)
#  transition.
# Now, to calculate the Q and U of the light BEFORE it gets weirded up
#  by the half-wave plate, we multiply Q by a [+1,-1] square wave to
#  approximately fix the rotation that the half-wave plate puts on,
#  the square wave having the period of the (high,low) transitions.
#  The square wave for U is the same as for Q, just phase-shifted by
#  half a hump.
# We take the mean of (data * square wave) to approximate the Q and U.
#  We also want to find T, intensity, but that's easy: just the mean
#  value of the data channel over the revolution.
#
# So! In total, what we do is this:
#  Read revolutions from a .dat file.
#  Make two copies of each channel's data.
#  Multiply each copy by a square wave.
#  Average the multiplied value over each revolution (and average the
#    unmultiplied original value).
#  Return an array 49 elements wide:
#    (revolution number + mean TQU of each channel) for each revolution.
#

from __future__ import division
import os
import numpy
import math
import glob
import ConfigParser

import datparsing

channels_labels = []
for ch in datparsing.channels_labels:
    for c in 'TQU':
        channels_labels.append(ch+c)
demod_dtype = numpy.dtype( [('rev',numpy.float)] + [(ch,numpy.float) for ch in channels_labels] )

global phases
phases = ConfigParser.ConfigParser(dict(((ch,'0') for ch in datparsing.channels_labels)))
def update_phases():
    """Updates the channel phase calibration data from phases.cfg."""
    global phases
    if not os.path.exists('phases.cfg'):
        print "Warning: no file named 'phases.cfg' found. All phases set to 0."
    phases.read('phases.cfg')
update_phases()


def square_wave(phase=0, U=False):
    """Returns a [+1,-1] square wave with 4 periods over SAMPLES_PER_REVOLUTION points.
    
    One of the rising edges is 'phase' data points in. If U==True, the rising edge
     is further offset by a quarter-period."""
    # We have 4 periods because, as explained at the top of the file,
    #  there are four [high,low] periods in each revolution.
    # The width of one flat section of square wave:
    width = datparsing.SAMPLES_PER_REVOLUTION // 8
    if U:
        phase += width // 2
    commutator = numpy.array([])
    for i in range(8):
        sign = -1 if (i%2) else 1
        commutator = numpy.concatenate([commutator, sign * numpy.ones(width)])
    return numpy.roll(commutator,phase)



def demodulate(raw):
    data = numpy.concatenate(tuple(datparsing.iter_valid_revolutions(raw)))
    result = numpy.zeros(len(data), dtype=demod_dtype)
    result['rev'] = data['rev']
    for ch in datparsing.channels_labels:
        phase = phases.getint('DEFAULT', ch)
        q_commutator = square_wave(phase=phase)
        u_commutator = square_wave(phase=phase, U=True)
        result[ch+'T'] = numpy.mean(data[ch], axis=1)
        result[ch+'Q'] = numpy.mean(data[ch]*q_commutator, axis=1)
        result[ch+'U'] = numpy.mean(data[ch]*u_commutator, axis=1)
    return result

def demodulate_dat(filename):
    return demodulate(datparsing.read_raw(filename))


if __name__ == '__main__':
    from GUI import application
    from GUI.FileDialogs import request_old_files
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
    from cofe_io import fits as fitsio

    application()
    refs = request_old_files()
    for ref in refs:
	fname = ref.path.replace('.dat','.fits')
        fitsio.write_fits(fname, {'DATA': demodulate_dat(ref.path)})
