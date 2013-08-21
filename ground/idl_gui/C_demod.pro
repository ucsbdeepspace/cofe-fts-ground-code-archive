function C_demod,indata, phase=phase,commutator=commutator


nptsperrev=256
nrevs=n_elements(indata.revolution)
nchan=n_elements(indata.data(*,0,0))
ph=fltarr(16)
if not(keyword_set(phase)) then phase = 0

; make the lockin function for one revolution

commutator=fltarr(nptsperrev)
eighth=floor(nptsperrev/8.)
commutator(0:eighth-1)=1
commutator(eighth:2*eighth-1)=-1
commutator(2*eighth:3*eighth-1)=1
commutator(3*eighth:4*eighth-1)=-1
commutator(4*eighth:*)=commutator(0:4*eighth-1)

;demodulate and integrate the signal
ideal=fltarr(nchan,3,nrevs)
for chan=0,nchan-1 do begin
    for i=0l,nrevs-1 do begin
       ideal(chan,0,i)=mean(reform(indata.data(chan,*,i)))
       ideal(chan,1,i)=mean(reform(indata.data(chan,*,i))*shift(commutator,phase))
       ideal(chan,2,i)=mean(reform(indata.data(chan,*,i))*shift(commutator,phase+32))
    endfor
endfor
outstruct=create_struct('Demod',ideal,'revolution',indata.revolution)
return, outstruct
end


