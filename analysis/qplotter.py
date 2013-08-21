import pylab
import numpy
import Release
import sys
import os
import glob

fnames = sorted(glob.glob(os.path.join(sys.argv[1],'*.dat')))
channel = 'Channel_%02dQ' %int(sys.argv[2])

data = numpy.zeros(0, dtype=Release.analysis.demodulation.demod_dtype)
for f in fnames:
    data = numpy.concatenate((data,Release.analysis.demodulation.demodulate_dat(f)))

starts = range(0,len(data),25)
avg = numpy.zeros(len(starts), dtype=data.dtype)
for avgi,dati in enumerate(starts):
    window = data[dati:dati+25]
    for channel in ('rev',channel):
        avg[avgi][channel] = numpy.mean(window[channel])
#print data.shape, avg.shape

pylab.figure()
pylab.scatter(avg['rev'], avg[channel])
pylab.show()