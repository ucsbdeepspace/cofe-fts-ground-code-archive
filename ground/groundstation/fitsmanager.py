import glob
import numpy
import os
import sys
import datetime
import threading
import time

_here = os.path.dirname(__file__)
sys.path.append(os.path.join(_here,'..','..'))
from devices import DEVICES
from cofe_io import fits as fitsio
from analysis import reshaping

def path_to_datetime(path):
    """Returns the folder/filename of the given path as a datetime object.
    
    The folder name is interpreted as YYYYMMDD[...], the filename
    as HHMMSS[...].
    
    """
    folder,filename = path.split(os.path.sep)[-2:]
    y,m,d = map(int,(folder[:4], folder[4:6], folder[6:8]))
    H,M,S = map(int,(filename[:2], filename[2:4], filename[4:6]))
    return datetime.datetime(y,m,d,H,M,S)
    
def paths_in_time_range( paths, start, end ):
    """Returns the set of given paths between the start and end times."""
    return filter((lambda p: (start < path_to_datetime(p) < end)), paths)

def mean( data ):
    """Returns the mean of a one-dimensional array.
    
    Even one with flexible type. Whatever that means."""
    result = numpy.zeros(1, dtype=data.dtype)
    for name in data.dtype.names:
        result[name] = numpy.mean(data[name])
    return result

class ConversionThread( threading.Thread ):
    """Thread to continuously convert spaceball files in a given directory.
    
    Only .spaceball files two levels below the given root are converted.
    
    """
    daemon = True
    def __init__( self, folder ):
        threading.Thread.__init__( self )
        self.folder = folder
        self.cancelled = False
        self.conversion_lock = threading.Lock()
    
    def convert_files( self, files, clobber=False ):
        """Converts a bunch of files into _ext.fits files."""
        self.conversion_lock.acquire()
        for f in files:
            # Since we have multiple threads going, the file may have
            #  been renamed (say, from .spaceball to .spaceball.bad)
            #  since our caller checked. Let's just print a warning
            #  if that's the case -- no need to end the program.
            if os.path.exists(f):
                reshaping.convert_file(f, clobber=clobber)
            else:
                print "WARNING: {0} does not exist".format(f)
            
        self.conversion_lock.release()

    def run( self ):
        while not self.cancelled:
            # We want to turn every spaceball file two levels below us
            #  into an _ext.fits file. We do it one at a time because
            #  if somebody calls our convert_files method, we assume
            #  they're higher-priority than our passive background
            #  conversion, and let them start their block as quickly
            #  as possible.
            spaceballs = glob.glob(os.path.join(self.folder,'*',
                                                 '*.spaceball'))
            for f in spaceballs:
                if self.cancelled:
                    return
                self.convert_files([f])
            time.sleep(5)
    
    def cancel( self ):
        self.cancelled = True

class GlobUpdateThread( threading.Thread ):
    interval = 3
    def __init__( self, callback, pattern):
        self.callback = callback
        self.pattern = pattern
        threading.Thread.__init__( self )
    def run( self ):
        while True:
            g = glob.glob(self.pattern)
            g.sort()
            self.callback(g)
            time.sleep(self.interval)
            


class FitsManager( object ):
    """Loads data from files and adds it to devices."""
    def __init__( self, folder ):
        self.folder = folder
        self.convert = False
        self.converter = None
        self.spaceballs = []
        self.exts = []
        GlobUpdateThread(self.update_spaceball_list,
                         os.path.join(folder,'*','*.spaceball')).start()
        GlobUpdateThread(self.update_ext_list,
                         os.path.join(folder,'*','*_ext.fits')).start()
        
        self.data = {}

        self.start = None
        self.end = None
        self.averaging = False
        
        self.listeners = []

    def set_interval( self, start, end ):
        """Sets the time range to load data from."""
        self.start = start
        self.end = end
    def set_convert( self, convert ):
        self.convert = convert
        if convert:
            self.converter = ConversionThread(self.folder)
            self.converter.start()
        else:
            self.converter.cancel()
    
    def update_spaceball_list( self, files ):
        self.spaceballs = files
    def update_ext_list( self, files ):
        self.exts = files
    
    def get_last_filetime( self ):
        last_file = self.spaceballs[-1]
        return path_to_datetime(last_file)
        
    def notify_listeners( self ):
        for listener in self.listeners:
            if hasattr(listener, 'note_manager_updated'):
                listener.note_manager_updated()

    def read_data( self ):
        """Loads the data in current time range and adds it to devices."""
        # First, convert any spaceballs in the given time range,
        #  IF we should (i.e. if the files are on the local drive)
        if self.convert:
            print "Converting relevant spaceballs..."
            print " (between {0} and {1})".format(self.start,self.end)
            spaceballs = paths_in_time_range(self.spaceballs,
                                             self.start, self.end)
            self.converter.convert_files(spaceballs)
            print "Converted."
        
        
        # Now we read the .fits files.
        files = paths_in_time_range(self.exts, self.start, self.end)

        if len(files) == 0:
            print "No files are in the given time range."
            return

        self.load_files_and_forget_others(files)
        self.set_device_data()
        self.notify_listeners()

    def set_device_data( self ):
        print "Setting device data..."
        # Clear all previously collected data from the devices and
        #  replace it with the concatenation of all the data from
        #  the files we've loaded.
        for device in DEVICES.itervalues():
            device.clear_data()
            for file,data in sorted(self.data.items()):
                if device.name in data:
                    device.add_data( data[device.name] )
        print "Done setting device data."

    def load_files( self, files ):
        new_files = [f for f in files if f not in self.data]
        print "Loading %d files..." %len(new_files)
        for file in new_files:
            file_data = fitsio.read_fits(file, primary=False)
            for ext,data in file_data.items():
                if data is None:
                    file_data.pop(ext)
                elif self.averaging:
                    file_data[ext] = mean(data)
            self.data[file] = file_data
        print "Finished loading."

    def forget_files( self, files ):
        for file in files:
            self.data.pop(file,None)
    def clear_cache( self ):
        self.data = {}
        
    def load_files_and_forget_others( self, files ):
        self.forget_files([f for f in self.data.keys() if f not in files])
        self.load_files(files)

