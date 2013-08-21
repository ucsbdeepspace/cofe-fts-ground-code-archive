# This file defines the Device and Channel objects, and creates the necessary
#  Devices and Channels for flight.
#
# A Device has a name, a display name, and a bunch of channels. The name is
#  the name for it used in the _ext.fits files, the display name is the name
#  we show on the screen, and the channels correspond to a subset of the
#  data channels the physical device provides.
#
# A Channel has a name and display name, like a Device. It also has a pointer
#  to the Device it belongs to. Channels also have read-only data attributes,
#  which just point to the appropriate field of the Device data.
# A Channel's name must be the name of one of the data channels provided by
#  the device (more technically, one of the column names in the _ext.fits
#  files produced by reshaping.convert_file).
#

import volts_to_temp
import ConfigParser
import numpy

def increasing_indices( array ):
    """Returns the indices of the given array that make it strictly increasing."""
    current_max = array[0]
    result = [0]
    for i,x in enumerate(array[1:]):
        if x > current_max:
            current_max = x
            result.append(i)
    return result

class Device( object ):
    """Represents a physical device from which data is gathered."""
    CLOCK_CHANNEL_NAME = 'computerClock'
      # Every device has a 'computerClock' channel stamped onto it by the
      #  flight computer when data is gathered. This allows us to
      #  synchronize the data we collect between devices.
    def __init__( self, name, display_name, channel_names ):
        self.name = name
        self.display_name = display_name
        
        channel_names = (Device.CLOCK_CHANNEL_NAME,) + tuple(channel_names)
        self.channel_names = tuple(channel_names)

        self.channels = {}
        for cname in channel_names:
            cdname = self.channel_name_to_display_name(cname)
            self.channels[cname] = Channel(cname, cdname, self)
        
        self.data = None
            
    def __str__( self ):
        return "<Device: %s>" %self.display_name
    def __repr__( self ):
        return str(self)
    
    def get_clock_channel( self ):
        """Returns the channel object associated with the clock count."""
        return self.channels[Device.CLOCK_CHANNEL_NAME]
    
    def iterchannels( self, clock=True ):
        """Returns a generator that iterates over the device's channels."""
        # clock is whether we should yield the clock channel, whose name is
        #  at the beginning of our channel name list.
        cnames = self.channel_names if clock else self.channel_names[1:]
        for cname in cnames:
            yield self.channels[cname]
                
    def add_data( self, data ):
        """Divides the data into channels and adds that data to the channels' data"""
        data = self.process(data)
        if len(data) > 0:
            if self.data is None:
                self.data = data
            else:
                self.data = numpy.concatenate((self.data,data))
            
    def process( self, data ):
        """Processes the given data, automatically called by add_data.
        
        Implemented as "return data". May be overridden by subclasses.
        
        """
        return data
    def process_retroactive( self ):
        """Replaces self.data with self.process(self.data)"""
        self.data = self.process(self.data)
    
    def clear_data( self ):
        """Clears all stored data."""
        self.data = None
    
    def channel_name_to_display_name(self, channel_name):
        """Returns a unique channel display name used in the GUI."""
        prefix = "%s " %self.display_name
        if channel_name == self.CLOCK_CHANNEL_NAME:
            return prefix + 'clock'
        return prefix + channel_name
            
            
class AnalogChannels( Device ):
    sensor_names = { 0:'i', 1:'c', 2:'h', 3:'l', 4:'k', 5:'e',
                     6:'d', 7:'n', 8:'b', 9:'a', 10:'f' }
    def process( self, data ):
        """Convert voltages of temperature channels to temperatures."""
        data = data.copy()
        for ind,name in self.sensor_names.iteritems():
            channel = self.channel_names[ind+1]
            data[channel] = volts_to_temp.convert(data[channel], name)
        return data
    
    def channel_name_to_display_name( self, channel_name ):
        # We measure lots of different things with the analog channels.
        # Just gotta have a giant switch statement.
        if channel_name.startswith("Channel"):
            i = int(channel_name[-2:])
            if i < 6:
                return "10GHz T%d" %(i+1)
            elif i < 11:
                return "15GHz T%d" %(i-5)
            elif i == 11:
                return "TSS 10GHz Dewbox"
            elif i == 12:
                return "TSS 15GHz Dewbox"
            elif i < 21:
                return "Ambient T%d" %(i-12)
            elif i == 21:
                return "I Servo +17V"
            elif i == 22:
                return "I 15GHz +17V"
            elif i == 23:
                return "I 30V rail"
            elif i == 24:
                return "I 10GHz +17V"
            elif i == 25:
                return "V Servo +17V"
            elif i == 26:
                return "V 15GHz +17V"
            elif i == 27:
                return "V 30V rail"
            elif i == 28:
                return "V 10GHz +17V"
            elif i == 29:
                return "Develco Max X"
            elif i == 30:
                return "Develco Max Y"
            elif i == 31:
                return "Develco Max Z"
        return Device.channel_name_to_display_name(self,channel_name)

class Telescope( Device ):
    parser = ConfigParser.ConfigParser()
    parser.optionxform = str
    parser.read('calibration.cfg')
    
    def __init__( self, revcounter, *args, **kwargs ):
        self.revcounter = revcounter
        self.sync = False
        Device.__init__( self, *args, **kwargs )
        
    def channel_name_to_display_name( self, channel_name ):
        if channel_name.startswith('Channel_'):
            return "%s %s" %(self.display_name,channel_name[-3:])
        return Device.channel_name_to_display_name(self,channel_name)
    
    def process( self, data ):
        """Adjusts the gains on all channels, and syncs the clock data."""
        data = data.copy()
        if self.parser.has_section(self.name):
            for channel,factor in parser.items(self.name):
                data[channel] *= float(factor)
        
        if self.sync and (self.revcounter.data is not None):
            our_revs = data['rev']
            other_revs = self.revcounter.data['value']
            other_times = self.revcounter.data[self.CLOCK_CHANNEL_NAME]

            keep_indices = increasing_indices(other_revs)
            other_revs = other_revs[keep_indices]
            other_times = other_times[keep_indices]
            data[CLOCK_CHANNEL_NAME] = numpy.interp( our_revs,
                                                     other_revs,
                                                     other_times )
        return data
        


class Channel( object ):
    """A stream of data coming in from a particular device."""
    def __init__( self, name, display_name, device ):
        self.name = name
        self.display_name = display_name
        self.device = device
        
    def __str__( self ):
        return "<Channel: %s>" %self.display_name
    def __repr__( self ):
        return str(self)
    
    # If you don't know what the @property decorator does:
    # it essentially overrides __getattr__ for an attribute
    # of the function name. So "@property; def attr(self):..."
    # allows you to say things like "x = inst.attr", but not
    # "inst.attr = 5".
    @property
    def data( self ):
        """Provides read-only access our column of the device's data."""
        if self.device.data is None:
            return None
        else:
            return self.device.data[self.name]
        
        

GYRO_HID = Device(
    'GYRO_HID', 'Gyro HID',
    ('HybridLatitude', 'HybridLongitude', 'HybridAltitude',
     'HybridNorthVelocity', 'HybridEastVelocity',
     'HybridVerticalVelocity', 'HybridHeadingAngle',
     'HybridPitchAngle', 'HybridRollAngle', 'HybridYawAngle',
     'HybridFOM') )
GYRO_MCD = Device(
    'GYRO_MCD', 'Gyro MCD',
    ('ModeStatusWord',) )
MAGNETOMETER = Device(
    'MAGNETOMETER', 'Magnetometer',
    ('heading', 'pitch', 'roll') )
ASHTECH = Device(
    'ASHTECH', 'Ashtech',
    ('GPSTime', 'heading', 'pitch', 'roll', 'baseline',
     'reset', 'latitude', 'longitude', 'altitude') )
ANALOGCHANNELS = AnalogChannels(
    'ANALOGCHANNELS', 'Analog channels',
    tuple(('Channel_%02d' %i for i in range(32))) )
        
REVCOUNTER_10GHZ = Device(
    'REVCOUNTER_10GHZ', '10-GHz RevCounter', ('value',) )
REVCOUNTER_15GHZ = Device(
    'REVCOUNTER_15GHZ', '15-GHz RevCounter', ('value',) )

TELESCOPE_10GHZ = Telescope(
    REVCOUNTER_10GHZ, 'TELESCOPE_10GHZ', '10-GHz Telescope',
    tuple(('Channel_%02dT' %i for i in range(16))) + ('Rev',) )
TELESCOPE_15GHZ = Telescope(
    REVCOUNTER_15GHZ, 'TELESCOPE_15GHZ', '15-GHz Telescope',
    tuple(('Channel_%02dT' %i for i in range(16))) + ('Rev',) )

CLOCKSYNC = Device(
    'CLOCKSYNC', 'Clock sync', ('filetime',) )

DEVICES = dict(( (device.name, device) for device in
                 (GYRO_HID, GYRO_MCD, MAGNETOMETER, ASHTECH,
                  ANALOGCHANNELS, TELESCOPE_10GHZ, TELESCOPE_15GHZ,
                  REVCOUNTER_10GHZ, REVCOUNTER_15GHZ, CLOCKSYNC) ))


def channel_parallels( map, clock=False ):
    """Returns a dict d, where d[device][channel] == map(device,channel)."""
    # Useful for things like fields of checkboxes, one per channel.
    # clock is whether we include the clock channel for each device.
    result = {}
    for device in DEVICES.itervalues():
        result[device] = {}
        for channel in device.iterchannels(clock=clock):
            result[device][channel] = map(device,channel)
    return result
