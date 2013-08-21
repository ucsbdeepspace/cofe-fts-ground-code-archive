import sys
import os
import glob
from demodulation import demodulate_dat

sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
from cofe_io import fits

folder = sys.argv[1]
refs = sorted(glob.glob(os.path.join(folder, '*.dat')))
n_files = len(refs)

import pycfitsio

for n, ref in enumerate(refs):
    print("Processing %d/%d: %s" % (n, n_files, ref))
    fname = ref.replace('.dat','.fits')

    f = pycfitsio.create(fname)
    f.write_HDU('DATA', demodulate_dat(ref))
    f.close()
