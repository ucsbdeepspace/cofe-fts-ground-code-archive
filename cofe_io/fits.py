import pyfits
import numpy

def write_fits( filename, data ):
    """Writes the contents of a dict to a .fits file.
    
    The dict maps fits extension names onto one-dimensional arrays
    of floats.
    
    If rename_columns is given, it is used to map the dtype.names
    of the given arrays onto the column names used in each extension.
    
    """
    hdul = pyfits.HDUList()
    for ext_name, ext_array in data.items():
        columns = []
        for name in ext_array.dtype.names:
            column = pyfits.Column( name=name,
                                    format='E',
                                    array=ext_array[name] )
            columns.append(column)
        ext = pyfits.new_table(columns)
        ext.name = ext_name
        hdul.append(ext)
    hdul.writeto( filename, clobber=True )

def read_fits( filename, primary=True ):
    """Reads a .fits file into a dict: {ext_name : ext_data}"""
    result = {}
    pf = pyfits.open(filename)
    if not primary:
        pf = pf[1:]
    for ext in pf:
        result[ext.name] = numpy.array(ext.data)
        #print "%s dtype:"%filename, result[ext.name].dtype
    pf.close()
    return result


def concatenate_fits(folder):
    """Concatenates the data for every fits file in a given folder.
    
    Output file is <folder name>.fits.
    
    """
    outfilename = "%s.fits" % folder
    filenames = glob.glob(os.path.join(folder, '*.fits'))
    hdulist = pyfits.open(filenames[0])
    for f in filenames[1:]:
        ff = pyfits.open(f)
        for i in range(1, len(hdulist)):
            prevlength = len(hdulist[i].data)
            hdulist[i] = pyfits.new_table(hdulist[i].columns, nrows=prevlength + len(ff[i].data))
            hdulist[i].name = ff[i].name
            for name in hdulist[i].columns.names:
                hdulist[i].data.field(name)[prevlength:] = ff[i].data.field(name)
        ff.close()
    hdulist.writeto(outfilename, clobber=True)
