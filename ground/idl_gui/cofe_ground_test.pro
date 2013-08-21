PRO Cofe_Ground_Test_event, ev

 COMMON Draw_share, allsectid, Tid, Qid, maxid, chan, path, File_name, backid

   WIDGET_CONTROL, ev.TOP, GET_UVALUE=allsectid
   WIDGET_CONTROL, ev.ID, GET_UVALUE=uval
   chan=float(chan)
   maxid=float(maxid)
    CASE uval OF
      'Get_File' : BEGIN
         cd, path
         crap=file_search('*.dat')
         dd=sort(crap)
         ddd=crap[dd]
         df=ddd[n_elements(ddd)-(backid+1)]
         result=file_info(df)
         if result.size lt 1000.0 then df=ddd[n_elements(ddd)-(backid+2)]
         WIDGET_CONTROL, File_name, SET_VALUE = df
         get_cofe_daq_x,d,files=df,/dontfix
         ddemod=c_demod(d,phase=maxid)
         WSET, allsectid
         ERASE
         plot,rebin(reform(d.data[chan,*,*]),256),/yn,/xs, background=0,color=5
         WSET, Tid
         ERASE
         plot,ddemod.demod[chan,0,*],/yn,/xs, background=0,color=5
         WSET, Qid
         ERASE
         polmin=min(ddemod.demod[chan,1:2,*])
         polmax=max(ddemod.demod[chan,1:2,*])
         plot,ddemod.demod[chan,1,*],/yn,/xs, yrange=[polmin,polmax],background=0,color=5
         oplot,ddemod.demod[chan,2,*],color=55
         End

         'NPS' : BEGIN
         cd, path
         crap=file_search('*.dat')
         dd=sort(crap)
         ddd=crap[dd]
         df=ddd[n_elements(ddd)-(backid+1)]
         result=file_info(df)
         if result.size lt 1000.0 then df=ddd[n_elements(ddd)-(backid+2)]
         WIDGET_CONTROL, File_name, SET_VALUE = df
         get_cofe_daq_x,d,files=df,/dontfix
         num=n_elements(d.data[0,0,*])
         c=reform(reform(d.data[chan,*,*],1,256.0*num))
         z=npsnoplot(c,256.0*30.0,.1)
         WSET, allsectid
         ERASE
         plot_io,z[*,0],z[*,1],/yn,/xs, background=0,color=5
         End
       'Max_Phase' : Begin
          WIDGET_CONTROL, ev.id, GET_VALUE = newname
          maxid = float(newname)
         END
       'Channel' : Begin
          WIDGET_CONTROL, ev.id, GET_VALUE = newname
          chan = float(newname)
         END
        'Back' : Begin
          WIDGET_CONTROL, ev.id, GET_VALUE = newname
          backid= float(newname)
         END
      'done' : WIDGET_CONTROL, ev.top, /DESTROY
   ENDCASE

END

PRO Cofe_Ground_Test, Dir_date=Dir_date

  COMMON Draw_share, allsectid, Tid, Qid, maxid, chan, path, File_name, backid
  loadmyctp
   if not(keyword_set(Dir_date)) then begin
      caldat,SYSTIME(/JULIAN, /UTC), month, day, year
      month=strcompress(string(month),/remove)
      year=strcompress(string(year),/remove)
      day=strcompress(strmid(systime(),8,2),/remove)
      if strlen(day) eq 1 then day=strcompress('0'+day,/remove)
      if strlen(month) eq 1 then month=strcompress('0'+month,/remove)
      Dir_date=strcompress(year+month+day,/remove)

    endif

    path='C:\Documents and Settings\Labuser\Desktop\test_data\'+strcompress(Dir_date,/remove_all)
    result=file_info(path)
    if not(result.exists) then path ='C:\Documents and Settings\Labuser\Desktop\test_data\20100601'
   main_base = WIDGET_BASE(/ROW,Title='Cofe Data Analysis', XSIZE=750, YSIZE=800)
   column1=widget_base(main_base,/column)
   text_allsect=widget_text(column1,value='.              All Sectors Averaged')
   draw_allsect = WIDGET_DRAW(column1, XSIZE=500, YSIZE=200)

   text_T=widget_text(column1,value='.                        Temperature')
   draw_T = WIDGET_DRAW(column1, XSIZE=500, YSIZE=200)

   text_Q=widget_text(column1,value='.                     Q (red) and U (blue)')
   draw_Q = WIDGET_DRAW(column1, XSIZE=500, YSIZE=200)

   button_base = WIDGET_BASE(main_base, /COLUMN)
   button = WIDGET_BUTTON(button_base, VALUE='Get File', $
      UVALUE='Get_File')

   button = WIDGET_BUTTON(button_base, VALUE='NPS', $
      UVALUE='NPS')

   button = widget_button(button_base, VALUE='Done', $
      UVALUE='done')
     column3=widget_base(main_base,/column)
    Title_Chan=widget_text(column3,value='Channel')
    Channel = WIDGET_TEXT(column3, $      ;This widget belongs to row1.
       /EDITABLE, $     ;Make the text field editable.
       XSIZE = 10, $
       YSIZE = 1, $
       UVALUE = 'Channel', $
       VALUE= '0')   ;The User Value for the widget.

  Title_phase=widget_text(column3,value='Maxphase')
  Max_phase = WIDGET_TEXT(column3, $      ;This widget belongs to row1.
       /EDITABLE, $     ;Make the text field editable.
       XSIZE = 10, $
       YSIZE = 1, $
       UVALUE = 'Max_Phase', $
       VALUE='0')   ;The User Value for the widget.

   Title_Back_files=widget_text(column3,value='Back Files')
   Back = WIDGET_TEXT(column3, $      ;This widget belongs to row1.
       /EDITABLE, $     ;Make the text field editable.
       XSIZE = 10, $
       YSIZE = 1, $
       UVALUE = 'Back', $
       VALUE='0')   ;The User Value for the widget.

   File_name=widget_text(column3,uvalue='File_name')


   WIDGET_CONTROL, main_base, /REALIZE
   WIDGET_CONTROL, draw_allsect, GET_VALUE=allsectid
   WIDGET_CONTROL, draw_T, GET_VALUE=Tid
   WIDGET_CONTROL, draw_Q, GET_VALUE=Qid
   WIDGET_CONTROL, channel, GET_VALUE=chan
   WIDGET_CONTROL, Max_phase, GET_VALUE=maxid
   WIDGET_CONTROL, back, GET_VALUE=backid
   WIDGET_CONTROL, main_base, SET_UVALUE=allsectid

   XMANAGER, 'Cofe_ground_test', main_base, /NO_BLOCK

END