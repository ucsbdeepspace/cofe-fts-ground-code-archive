import UniversalLibrary as UL
UL.cbDConfigPort(0,10,1)
print('You are starting at angle 0 degrees')
position=0
cmd='b'
angle=0.0
while cmd.lower() != 'q':
    print('Current position = '),position
    print('Current delta angle request = '),angle
    cmd=raw_input('What to do now? (a: choose angle, p:set position value here, g:go,s:stop moving! q:quit) ')
    if cmd.lower() == 'a':
        anglestring=raw_input('Input angle to move by in +- degrees ' )
        angle=float(anglestring)
    elif cmd.lower() == 'p':
        positionstring=raw_input('Input current position angle ' )
        position=float(positionstring)
    elif cmd.lower()=='q' :
        chk=raw_input('Really quit? (y,n) ')
        if chk.lower()!='y':
            cmd='b'
    elif cmd.lower()=='g' :
        npulses=int(abs(angle)*80)
        dir=0
        if angle < 0:
            dir=1 
        UL.cbDBitOut(0,10,1,dir)
        for i in range(0,npulses+1):
            try:
                UL.cbDBitOut(0,10,0,1)
                UL.cbDBitOut(0,10,0,0)
            except KeyboardInterrupt:
                break
        position=position+(1.-2.*dir)*i/80.

                

    