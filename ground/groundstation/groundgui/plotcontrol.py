# This file provides the plotting interface and functionality
#  for the groundstation.
# To do:
#   I'm not sure how to relabel the x-axis, but it would be good
#    to replace the current labels (minutes since computer turned on)
#    with HH:MM:SS, using the currently-unused clock_to_datetime
#    function. A possible implementation is described in
#    PlotControlWindow.plot().
#

import pylab
import datetime
import os
from wx import PyDeadObjectError

from GUI import Window, Button, CheckBox, RadioButton, RadioGroup, Row, Label

import devices
from devices import DEVICES, GYRO_HID, ASHTECH, MAGNETOMETER,\
    ANALOGCHANNELS, TELESCOPE_10GHZ, TELESCOPE_15GHZ, CLOCKSYNC
import ggutils
from ggutils import PADDING


CHECKBOX_LAYOUT = ( ( (GYRO_HID, 6), (ASHTECH, 6), (MAGNETOMETER, 6) ),
                    ( (ANALOGCHANNELS, 6), ),
                    ( (TELESCOPE_10GHZ, 6), (TELESCOPE_15GHZ, 6) ) )

COLOR_CYCLE = 'bgrcm'

def clock_to_minutes( ticks ):
    """Converts flight computer timestamp to minutes since turn-on."""
    return ticks * (1./60) * (2./10**9)

def filename_to_datetime(path):
    """Parses a YYYYMMDD/HHMMSS.whatever file path as a datetime."""
    filename = os.path.basename(path)
    folder = path.split(os.path.sep)[-2]
    return datetime.datetime(*map(int,[folder[:4],folder[4:6],folder[6:8],
                                        filename[:2],filename[2:4],
                                        filename[4:6]]))

_FILETIME_ZERO = datetime.datetime(1601,1,1,0,0,0)
def clock_to_datetime( cc ):
    """Converts a flight computer clock timestamp into a datetime.
    
    Uses the ClockSync device provided by the flight computer, which
    matches computerClock to filetime (100-ns increments since Jan 1,
    1601).
    
    """
    timestamps = CLOCKSYNC.get_clock_channel()
    filetimes = CLOCKSYNC.channels['filetime']
    ft = numpy.interp( cc, timestamps, filetimes )
    seconds = ft // 10**7
    return _FILETIME_ZERO + datetime.timedelta(seconds=seconds)

class Plot( object ):
    def __init__( self, device, channels ):
        self.device = device
        self.channels = channels

        self.lines = []
        minutes = clock_to_minutes(device.get_clock_channel().data)
        style_i = 0
        for channel in channels:
            marker_i,color_i = divmod(style_i, len(COLOR_CYCLE))
            line, = pylab.plot( minutes, channel.data, s=40,
                                c=COLOR_CYCLE[color_i],
                                label=channel.display_name )
            self.lines.append(line)
            style_i += 1
    
    def replot( self ):
        """Update open plot to reflect the currently loaded data."""
        minutes = clock_to_minutes(self.device.get_clock_channel().data)
        for line, channel in zip(self.lines, self.channels):
            line.set_data(minutes, channel.data)
        line.axes.relim()
        line.axes.autoscale_view(True, True, True)
        line.axes.figure.canvas.draw()

class PlotControlWindow( Window ):
    """Contains plotting option controls."""
    resizable = True
    live_plots = []
    
    def __init__( self, manager ):
        super(PlotControlWindow, self).__init__(title="Plot Control")
        
        # We'll need to be able to read data from (and be notified by)
        #  the FitsManager object in charge of the data.
        self.manager = manager
        
        self.checkboxes = devices.channel_parallels( (lambda d,c: CheckBox(c.display_name, font=ggutils.ENTRY_FONT)) )
        self.plot_button = Button( title='Plot', width=100, action=self.plot )
        
        self.build()
        
    def build( self ):
        """Lays out the components of the window."""
        box_frame = ggutils.frame_items(self.checkboxes, layout=CHECKBOX_LAYOUT)
        self.place( box_frame, left=PADDING, top=PADDING )
        self.place( self.plot_button, left=PADDING, top=box_frame.bottom+3*PADDING )
        self.shrink_wrap()
            
    def plot( self ):
        # For every checked checkbox, we plot that channel's value (Y)
        #  against that device's time channel (X).
        pylab.figure()
        style_i = 0
        for device, checkboxes in self.checkboxes.iteritems():
            plot_channels = [channel for channel,checkbox in checkboxes.iteritems()
                             if checkbox.value]
            if not plot_channels:
                continue
            if (device.data is None):
                print "No time data has been gathered on device {0}: cannot plot channels".format(device.name)
                continue
            # A possible implementation of the replacing-x-axis-labels code:
            #  <plot channels against clock_channel.data>
            #  for label in <x-axis labels>:
            #      timestamp = <somehow extract clock information from label>
            #      new_text = clock_to_datetime(timestamp)
            #      <label text> = new_text
            # I'm not sure how to read/write label text, though -- I haven't been
            #   able to get set_xticklabels to work the way I expect.
            # Also, not sure how to get clock information from the label, since
            #   the label isn't just the value at that position.
            live_plot = Plot(device, plot_channels)
            self.live_plots.append(live_plot)
      
        pylab.legend()
        pylab.grid()
        pylab.show()

    def plot_update(self):
        """Update open plots to reflect the currently loaded data."""
        dead_plots = []
        for live_plot in self.live_plots:
            try:
                live_plot.replot()
            except PyDeadObjectError:
                print "A plot was closed since we last updated it."
                dead_plots.append(live_plot)
                
        if dead_plots:
            print "Removing recently closed plots."
            for plot in dead_plots:
                self.live_plots.remove(plot)
                
