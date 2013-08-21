import numpy
import os

_CALNAME_FORMAT = os.path.join(os.path.dirname(__file__),
                               'cryo_temp_lookup_%s.txt')

global _calibration_data
_calibration_data = {}

def _parse_calibration_file(fname):
    f = open(fname)
    lines = f.readlines()
    f.close()
    lines = filter(None,[line.strip() for line in lines])
    pairs = [filter(None,line.split(' ')) for line in lines]
    pairs = [(v,t) for v,t in pairs if not t.endswith('NaN')]
    pairs = [(float(v),float(t)) for v,t in pairs]
    return pairs

def _set_calibration_data():
    global _calibration_data
    for name in list('abcdefghijklmn')+['m2','z']:
        fname = _CALNAME_FORMAT %name
        pairs = _parse_calibration_file(fname)
        pairs.sort()
        volts,temps = zip(*pairs)
        _calibration_data[name] = (volts,temps)

def convert(volts, name):
    global _calibration_data
    cal_volts, cal_temps = _calibration_data[name]
    return numpy.interp(volts, cal_volts, cal_temps)
    
_set_calibration_data()