import sys

phase = int(sys.argv[1])

f = open('phases.cfg','w')
f.write( '\n'.join( ['[DEFAULT]'] + ['Channel_%02d = %d' %(ch,phase) for ch in range(16)] ) )