#!/usr/bin/python
# This script will plot the T, Q, or U from one channel on a .fits file.
# Recommended usage is
#   signalplot.py -c CHANNEL_NUMBER -t TQU FILENAME
#  where FILENAME is a Level1 .fits file, TQU specifies which kind of data
#  you want plotted, CHANNEL_NUMBER is the index of the channel you want
#  to plot it from (0 to 15), and FILENAME is the name of the .fits file.
# The .fits file I'm testing this on has rather wonky time interpolation.
#  If that is still the case, throw a "-i" in there too, to plot against
#  data-point index rather than interpolated time.

import pylab
import numpy
import pyfits
import optparse

parser = optparse.OptionParser()
parser.add_option( '-c', '--channel', action='store',
                   dest='channel', type='int', default=1,
                   help="Specifies which channel's data to plot (0-15) (default 1)" )
parser.add_option( '-t', '--type', action='store',
                   dest='TQU', default='T',
                   help='Specifies the T, Q, or U channel to plot (default T)' )
parser.add_option( '-s', '--square', action='store_true',
                   dest='square',
                   help='Subtracts off the median value and squares the signal.' )
parser.add_option( '-i', '--index', action='store_true',
                   dest='index',
                   help='Plots signal against index rather than time' )
parser.add_option( '-o', '--offset', action='store',
                   type='int', dest='offset', default=0,
                   help='Chops off the first N data points' )
parser.add_option( '-n', '--no-lines', action='store_true',
                   dest='no_lines',
                   help='Plots with points instead of lines' )

options,args = parser.parse_args()
if len(args) != 1:
    raise RuntimeError("target filename must be provided")

h = pyfits.open(args[0],
                memmap=True)
time = h[1].data['UT'][options.offset:]
signal = h[2+options.channel].data[options.TQU][options.offset:]

if options.square:
    signal = (signal-numpy.median(signal))**2

format = 'g'
if options.no_lines:
    format += '.'

if options.index:
    pylab.plot(signal, format)
else:
    pylab.plot(time, signal, format)

pylab.show()
