from __future__ import division
from scipy import optimize
import sys
#put your path to demod
sys.path.append('/home/zonca/COFE/pyread/svn/')

import demod
d=demod.RawDataReader(['20101111/17464700.dat'])
raw=d.load_raw(d.filenames[0])

# create data matrix 1st col power, 2nd col volts
data=zeros([len(raw['ch0']),2])
data[:,0]=raw['ch1']
data[:,1]=65536- raw['ch0']
datas=np.sort(data,axis=0)

#linear fit
(ar,br)=polyfit(datas[:,0],datas[:,1],1)
linch0=polyval([ar,br],datas[:,0])

# model fit
def fitfunc(p, x):
    return p[0]/(1+p[1]*p[0]*(x+p[2]))*(x+p[2])
def errfunc(p, x, y):
    return fitfunc(p, x) - y
p0 = [ar,0.,br/ar]
p,success=optimize.leastsq(errfunc, p0[:], args=(datas[:,0],datas[:,1]),maxfev=5000)

# plots
plot(datas[:,0],datas[:,1],'.')
#plot(datas[:,0],linch0)
#plot(datas[:,0],fitfunc(p0,datas[:,0]),'k')
plot(datas[:,0],fitfunc(p,datas[:,0]),'m')
grid()
