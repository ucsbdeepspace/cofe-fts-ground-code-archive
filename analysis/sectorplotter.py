from __future__ import absolute_import
from . import datparsing
import numpy
import pylab
import sys

colors = 'rgbck'
    
def run(fname, channelnums):
    raw = datparsing.read_raw(fname)
    data = numpy.concatenate(tuple(datparsing.iter_valid_revolutions(raw)))
    means = numpy.zeros(1, dtype=datparsing.rev_dtype)[0]
    for ch in datparsing.channels_labels:
        #print means[ch].shape, data[ch].mean(axis=0).shape, data[ch].mean(axis=1).shape
        means[ch] = data[ch].mean(axis=0)

    sectors = pylab.arange(0,4096,4096//256)

    style_i = 0

    pylab.figure()
    for channelnum in channelnums:
        channel = datparsing.channels_labels[channelnum]
        print means[channel][0]
        print sectors
        pylab.plot(sectors,means[channel][0],c=colors[style_i%len(colors)], label=channel)
        style_i += 1

    pylab.legend()
    pylab.show()

if __name__ == '__main__':
    fname = sys.argv[1]
    channelnums = map(int, sys.argv[2:])
    run(fname, channelnums)
