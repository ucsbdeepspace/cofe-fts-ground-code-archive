PRO get_cofe_daq_x, alldata_s,keep=keep,files=files, endians=endians,sec_per_rev=sec_per_rev,rawchan=rawchan,dontfix=dontfix

;PRM modified 7/31/06, to make output a structure (to allow long integer for rev number)
;BDW modified 8/1/06 added section to remove bad sectors
;prm and bdw mod to keep only specified data channels 8/8/06
;BDW added line to print file names
;new version, 8/10/09 for COFE daq data files from Ryan code on flight computer(s)

;file has 25 2 byte numbers:3.

;first 16 numbers are analog data outputs
;next  2-byte number is encoder position
;next 5 2-byte numbers are ignored!?!
;last 3 2-byte numbers contain 24 bit rev number: low, middle high sections

;if not(keyword_set(endians)) then endians='big'
;default was 250 sectors/rev, now set a keyword:
;test version april 21 2010 getting rid of some unused channels, now 21 chans to read not 25 prm
;added kw dontfix (default is to fix bad revolutions)

if not(keyword_set(rawchan)) then rawchan=21
if not(keyword_set(sec_per_rev)) then sec_per_rev=256
secdiv=3+4096/sec_per_rev


if not(keyword_set(keep)) then keep=indgen(16)
nchan=n_elements(keep)

if not(keyword_set(files)) then files = dialog_pickfile(/multiple_files, title='Pick Data Files')

if total(strlen(files)) ne 0 then begin
    files = files(sort(files))
    for i=0l, N_ELEMENTS(files)-1 do begin
        print,files(i)
        stuff=file_info(files(i))
        npoints=stuff.size/(rawchan*2) ;bytes per raw channel x raw channels
        tempd=read_binary(files(i),data_type=12,data_dims=[rawchan,npoints],endian=endians)


        ;for variable type codes look in help under SIZE function
        npoints=n_elements(tempd[16,*])

        if i eq 0 then begin
            first_ramp=where(tempd(16,1:1000) lt secdiv)
            tempd=tempd[*,first_ramp[0]+1:*]

        endif else begin
            allpoints=n_elements(allsector[*])

            If abs(tempd(16,0)- allsector[allpoints-1]) gt secdiv then begin
                first_ramp=where(tempd(16,*) lt secdiv)
                tempd=tempd[*,first_ramp[0]:*]
                last_ramp=where(allsector[allpoints-(sec_per_rev-1):*] gt 4050)
                alldata=alldata[*,0:last_ramp[0]+allpoints-255]
                allsync=allsync[0:last_ramp[0]+allpoints-255]
                allsector=allsector[0:last_ramp[0]+allpoints-255]

            endif
        endelse

        temp_size=size(tempd)
        npoints=temp_size[2]
        ;nrev=fix(npoints/128)

        data=fltarr(nchan,npoints)
        print,npoints

        For k=0,nchan-1 do begin
            data[k,*]=(tempd[keep(k),*]*((20.)/(2.^16)))-10.
        endfor

        sector=tempd[16,*]
        syncnum_long=reform(long64(tempd(18,*))*1l+long64(tempd(19,*))*256l +long64(tempd(20,*))*256l*256l)
		;syncnum_long=reform(long64(swap_endian(tempd(18,*)))*1l+long64(swap_endian(tempd(19,*)))*256l +long64(swap_endian(tempd(20,*)))*256l*256l)
        if i eq 0 then begin
            alldata=data
            allsector=reform(sector)
            allsync=syncnum_long
        endif else begin
         alldata=[[alldata],[data]]
            allsector=[allsector,reform(sector)]
            allsync=[allsync,syncnum_long]
       endelse

    endfor
endif

allsize=size(alldata)
numrevs=floor(allsize[2]/sec_per_rev)
points=(numrevs*sec_per_rev)-1
;**********************
if not(keyword_set(dontfix)) then begin
    s=allsector[0:points]
    ns=n_elements(s)
    r=where(s[1:*]-s[0:ns-2] gt 3900)
    nr=n_elements(r)
    gr=where((r[1:nr-1]-r[0:nr-2]) eq sec_per_rev)      ;keep only revolutions with proper number of samples
    ngr=n_elements(gr)
    help,nr,gr
    newsectors=intarr(sec_per_rev,ngr)
    newdata=fltarr(nchan,sec_per_rev,ngr)
    newrevs=lonarr(ngr)
    for i=0l,ngr-1l do newsectors[*,i]=s[r(gr[i])+1:r(gr[i])+sec_per_rev]          ; now select out these revs for sector
    for i=0l,ngr-1l do newdata[*,*,i]=alldata[*,r(gr[i])+1:r(gr[i])+sec_per_rev]   ; now select out these revs for data
    for i=0l,ngr-1l do newrevs[i]=ulong(allsync[r(gr[i])+1])                       ; now select out these revs for revolutions
    numrevs=ngr
endif
if keyword_set(dontfix) then begin
    newdata=reform(alldata[*,0:points],nchan,sec_per_rev,numrevs)
    allsync=ulong(allsync(0:points))
    newrevs=sample_ulong(allsync,sec_per_rev,0)
    newsectors=reform(allsector[0:points],sec_per_rev,numrevs)
endif

alldata_s=create_struct('Data',newdata,'Sector',newsectors,'Revolution',newrevs)
End