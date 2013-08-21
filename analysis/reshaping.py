#!/usr/bin/env python
#
# This code converts .spaceball files into pretty .fits files.
#  The initial spaceball-to-fits conversion is done by a .exe
#  that lives somewhere else, but the .fits it produces are
#  super-ugly.
# This code provides the ability to read the super-ugly files
#  produced by Spaceball2FITS.exe and separates the data by
#  device into the extensions of a file named
#  <original_base>_ext.fits.
# So we end up with .fits files that have extensions named
#  things like "GYRO", "MAGNETOMETER", etc.
#

import subprocess
import os
import pyfits
import glob
import numpy

SPACEBALL2FITS_EXE = os.path.join(os.path.dirname(__file__),
                                  'Spaceball2FITS',
                                  'Spaceball2FITS.exe')

# We identify which device a set of data belongs to using
#  the number of fields.
device_names = {
        51 : 'Telescope',
        34 : 'AnalogChannels',
        31 : 'Gyro_MCD',
        16 : 'Gyro_HID',
        11 : 'Ashtech',
        9 : 'Magnetometer',
        3 : 'RevCounter'
        }

# There are two revolution counters and two telescopes,
#  so we figure out which is which by the "index" field
#  attached to the device by the servo computer.
# The indices are the (0-indexed) positions in the
#  devices.cfg file on the servo computer.
revcounter_freqs = { 
        1 : '10GHz',
        2 : '15GHz'
        }
telescope_freqs = {
        5 : '10GHz',
        6 : '15GHz'
        }

def pairwise(sequence):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..., (s[-2],s[-1])"""
    for i in range(len(sequence)-1):
        yield sequence[i], sequence[i+1]

def reshaped_filename(filename):
    return filename.replace('.fit','_ext.fits')

def is_converted(filename):
    if filename.endswith('.spaceball'):
        return os.path.exists(filename.replace('.spaceball','_ext.fits'))
    elif filename.endswith('fit'):
        return os.path.exists(filename.replace('.fit','_ext.fits'))
    else:
        return True

def separate_data( data ):
    result = []
    colnames = data.dtype.names
    boundaries = [i for i,colname in enumerate(colnames) if colname.endswith('computerClock')]
    boundaries.append(len(colnames))
    for start,end in pairwise(boundaries):
        number_of_fields = end-start
        if number_of_fields not in device_names.iterkeys():
            print "Warning: a device is providing %d fields, an unrecognized number." %number_of_fields
        device_name = device_names.get(number_of_fields, 'Device%d-%d' %(start,end))
        if device_name == 'RevCounter':
            try:
                index_field = data.field(start+1)
                revcounter_index = index_field[ numpy.nonzero(index_field)[0][0] ]
                freq = revcounter_freqs.get(revcounter_index, '%d-%d' %(start,end))
                device_name = device_name + '_' + freq
            except IndexError:
                print('RevCounter with index %d is probably OFF, REMOVED from the fits file' %start)
                continue
        elif device_name == 'Telescope':
            try:
                index_field = data.field(start+1)
                telescope_index = index_field[ numpy.nonzero(index_field)[0][0] ]
                freq = telescope_freqs.get(telescope_index, '%d-%d' %(start,end))
                device_name = device_name + '_' + freq
            except exceptions.IndexError:
                print('Telescope with index %d is probably OFF,'
                       ' REMOVED from the fits file' % start)
                continue
        result.append((device_name, slice(start,end)))

    return result

def reshape_fits( filename ):
    extension = pyfits.open(filename, ignore_missing_end=True)[1]
    newfile = pyfits.HDUList()
    for name,range in separate_data(extension.data):
        print(name)
        new_columns = []
        for col in extension.columns[range]:
            new_name = col.name.partition('_')[2]
            new_name = new_name.replace(' ','_')
            new_column = pyfits.Column( name=new_name,
                                        format=col.format,
                                        array=col.array )
            new_columns.append(new_column)
        newext = pyfits.new_table(new_columns)
        newext.data = purge_zeros(newext.data)
        newext.name = name
        newfile.append(newext)
    newfilename = filename.replace('.fit', '_ext.fits')
    newfile.writeto(newfilename, clobber=True)

def convert_spaceball(filename):
    """Converts <name>.spaceball to <name>.fit.
    
    Returns True if the conversion is successful. Otherwise, renames
    the file to <name>.spaceball.bad and returns False.
    
    """
    base = filename.rpartition('.')[0]
    subprocess.call([SPACEBALL2FITS_EXE, filename])
    if not os.path.exists(base+'.fit'):
        print "Conversion of {0} unsuccessful. Renaming to {1}"\
                    .format(filename, filename+'.bad')
        try:
            os.rename(filename, filename+'.bad')
        except WindowsError:
            print "Whoops! Never mind, it's busy. Oh well."
        return False
    return True

def convert_file(filename, clobber=False):
    """Converts a .spaceball or .fit into a _ext.fits."""
    base = filename.rpartition('.')[0]
    if not os.path.exists(filename):
        raise ValueError("{0} does not exist.".format(filename))
        
    if filename.endswith('.spaceball'):
        if clobber or not os.path.exists(base+'.fit'):
            success = convert_spaceball(filename)
            if success:
                convert_file(base+'.fit')
    elif filename.endswith('.fit'):
        if clobber or not os.path.exists(base+'_ext.fits'):
            reshape_fits(filename)

def convert_folder(folder, clobber=False):
    """Calls convert_file on every .spaceball or .fit in the folder."""
    spaceballs = glob.glob(os.path.join(folder,'*.spaceball'))
    fits = glob.glob(os.path.join(folder,'*.fit'))
    for f in spaceballs+fits:
        convert_file(f, clobber=clobber)

def purge_zeros(data):
    return data[data.field(0) != 0]


if __name__ == '__main__':
    from GUI import application
    from GUI.FileDialogs import request_old_directory
    application()
    convert_folder(request_old_directory().path)
