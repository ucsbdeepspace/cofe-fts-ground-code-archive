import os
import sys
import numpy
import pyfits

sys.path.append(os.path.join(sys.path[0],'..','..','telescope'))
import demodlib

def data_to_voltage( data ):
    return data.astype(numpy.float) * 20./(2**16) - 10

def fits_format( filename ):
    sections = pyfits.open(filename)
    section_names = [s.name for s in sections]
    if section_names[1] == 'DATA':
        return 'telescope'
    elif any((n.startswith('TELESCOPE') for n in section_names)):
        return 'ground'
    else:
        raise ValueError("Unable to determine format of %s: section names are %s" %(filename,str(section_names)) )

def formal_name( format, channelstr ):
    if format == '.dat':
        # Should just be an integer.
        try:
            n = int(channelstr)
            if not (0 <= n < 16):
                raise ValueError
        except ValueError:
            raise ValueError('For .dat files, channels must be <int 0-15>, e.g. 12')
        return 'ch%d' %n
    elif format.endswith('.fits'):
        # Should be of form "0T", "12Q", etc.
        try:
            n = int(channelstr[:-1])
            c = channelstr[-1]
            if (c not in 'TQU') or not (0 <= n < 16):
                raise ValueError
        except ValueError:
            raise ValueError('For telescope .fits files, channels must be <int 0-15><TQU>, e.g. 12Q')
        if format.startswith('telescope'):
            return 'ch%d_%s'%(n,c)
        elif format.startswith('ground'):
            return 'Channel_%d%s'%(n,c)
    raise ValueError("Unknown file format: %s" %str(format) )

def fileformat( filename ):
    if filename.endswith('.dat'):
        return '.dat'
    elif filename.endswith('.fits'):
        return fits_format(filename) + '.fits'
    else:
        raise ValueError("Unknown file format: %s" %str(filename))

def read_data( filerefs, channelstrs, frequency=10 ):
    result = dict(( (channelstr, numpy.array([])) for channelstr in channelstrs ))
    format = fileformat( filerefs[0].path )
    formal = dict(( (channelstr,formal_name(format, channelstr))
                    for channelstr in channelstrs ))
    print "format =", format
    print "formal =", formal
    if format == '.dat':
        raw_data = demodlib.read_raw_data([f.path for f in filerefs])
        for channelstr in channelstrs:
            print "Formal:", repr(formal[channelstr])
            print raw_data[formal[channelstr]].shape
            channel_data = numpy.concatenate(raw_data[formal[channelstr]])
            result[channelstr] = data_to_voltage(channel_data)
    elif format.endswith('.fits'):
        for fileref in filerefs:
            pf = pyfits.open(fileref.path)
            if format == 'telescope.fits':
                data = numpy.array(pf[1].data)
            elif format == 'ground.fits':
                device = 'TELESCOPE_%DGHZ' %frequency
                data = [ext.data for ext in pf if ext.name == device]
                if data:
                    assert len(data) == 1
                    data = data[0]
                else:
                    print "No extension %s in %s" %(device,fileref.path)
                    continue
                
            for channelstr in channelstrs:
                channel_data = numpy.concatenate(data[formal[channelstr]])
                result[channelstr] = numpy.concatenate((result[channelstr],
                                                        channel_data))
    else:
        raise AssertionError('Format %s is unrecognized. My bad.' %type)
    return result

def write_data(filename, arrays):
    if not os.path.exists('Power spectra'):
        os.mkdir('Power spectra')
    toname = os.path.join('Power spectra', filename+'.powspec')
    f = open(toname,'w')
    for array in arrays:
        f.write( ', '.join((str(float(x)) for x in array)) )
        f.write( '\n' )
    f.close()
