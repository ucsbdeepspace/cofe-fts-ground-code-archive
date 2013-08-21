import matplotlib
import pylab
import sys
import os
import numpy
import psio

blackman = (lambda x: x * numpy.blackman(len(x)))
hamming = (lambda x: x * numpy.hamming(len(x)))
bartlett = (lambda x: x * numpy.bartlett(len(x)))

def plot( pairs, options ):
    pylab.figure()
    for filelist,channellist in pairs:
        data = psio.read_data( filelist, channellist )
        for channel,voltages in data.iteritems():
            if len(filelist) == 1:
                fname = filelist[0].name
            else:
                fname = '-'.join((filelist[0].name, filelist[-1].name))
            title = ' '.join((fname, str(channel)))
            if options['against_time']:
                plot_voltages(voltages, title, options)
            else:
                plot_psd(voltages, title, options)

    configure_axes(options)
    pylab.legend()
    pylab.show()

def configure_axes( options ):
    axes = pylab.gca()
    axes.set_xscale(options['xscale'])
    axes.set_yscale(options['yscale'])
    if options['against_time']:
        axes.set_xlabel('Sample number')
        axes.set_ylabel('Voltage')
    else:
        if options['sqrt']:
            axes.set_ylabel('Power density (V (Hz^.5))')
        else:
            axes.set_ylabel('Power density (V^2 Hz)')
            
    axes.autoscale_view()


def plot_psd( voltages, title, options ):
    nfft = int(options['frequency']/options['resolution'])
    detrend = matplotlib.mlab.detrend_none if (options['detrending']=='none')\
        else matplotlib.mlab.detrend_mean if (options['detrending']=='mean')\
        else matplotlib.mlab.detrend_linear
    window = matplotlib.mlab.window_hanning if (options['windowing']=='hanning')\
        else matplotlib.mlab.window_none if (options['windowing']=='none')\
        else blackman if (options['windowing']=='blackman')\
        else hamming if (options['windowing']=='hamming')\
        else bartlett
    
    pxx, freqs = matplotlib.mlab.psd( voltages, NFFT=nfft,
                                      Fs=options['frequency'],
                                      detrend=detrend,
                                      window=window )

    y = pylab.sqrt(pxx) if options['sqrt'] else pxx
    pylab.plot( freqs, y, label=title )
    psio.write_data( title, (freqs, pxx) )

def plot_voltages( voltages, title, options ):
    pylab.plot( voltages[options['slice']], label=title )
    
