import pylab
import pickle
import sys

colors = 'bgrck'
markers = 'so^+'

def plot(channel_phase_info, channelnums):
    pylab.figure()
    i = 0
    for channelnum in channelnums:
        channel = 'Channel_%02d'%channelnum
        pairs = channel_phase_info[channel].items()
        x = [phase for phase,mean in pairs]
        y = [mean for phase,mean in pairs]
        style = colors[i%len(colors)] + markers[i//len(markers)]
        i += 1
        pylab.plot(x,y,style, label=channel)

    pylab.legend()
    pylab.show()
