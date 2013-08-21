PRO Cofe_Ground_Test_b_event, ev 
 
 COMMON wDraw_share2, main_base, allsectid, Tid, Qid, maxid, chan, path, File_name, backid, text_allsect,$
      drawid1, drawid2, drawid3, popup_file,text_T,fi
   ;WIDGET_CONTROL, ev.TOP, GET_UVALUE=allsectid 
   WIDGET_CONTROL, ev.ID, GET_UVALUE=eventval 
   chan=float(chan)
   maxid=float(maxid)

IF (TAG_NAMES(ev, /STRUCTURE_NAME) EQ 'WIDGET_TIMER')  THEN BEGIN
      
         d=get_demod_cofe(path=path,back_num=backid)
         fi=d.file
         WIDGET_CONTROL, popup_file, SET_VALUE = fi
         WSET, drawid1
         ERASE 
         plot,rebin(reform(d.data[chan,*,*]),256),/yn,/xs, background=0,color=5
         WSET, drawid2
         ERASE 
         plot,d.demod[chan,0,*],/yn,/xs, background=0,color=5
         WSET, drawid3
         ERASE 
         polmin=min(d.demod[chan,1:2,*])
         polmax=max(d.demod[chan,1:2,*])
         plot,d.demod[chan,1,*],/yn,/xs, yrange=[polmin,polmax],background=0,color=5
         oplot,d.demod[chan,2,*],color=55   
         WIDGET_CONTROL, ev.id, TIMER=10.0
ENDIF else begin

 CASE eventval OF      
     'popup':     BEGIN
        popupbase = WIDGET_BASE(/row,xsize=600,ysize=800)
        column_popup=widget_base(popupbase,/column)
        text_1=widget_text(column_popup,value='.              All Revolutions Averaged')
        popupdraw1=widget_draw(column_popup,xsize=500,ysize=200)
        text_1=widget_text(column_popup,value='.              Temperature')
        popupdraw2=widget_draw(column_popup,xsize=500,ysize=200)
        text_1=widget_text(column_popup,value='.              Q (black) and U (Blue)')
        popupdraw3=widget_draw(column_popup,xsize=500,ysize=200)
        Popup_file=widget_text(column_popup,value=' ',xsize=25)
        popupbutton = WIDGET_BUTTON(popupbase,UVALUE = 'GOBACK',VALUE = 'Go Back',XSIZE=75, YSIZE=75)
        buttonSTM = WIDGET_BUTTON(button_base, VALUE='Save to Main', UVALUE='STM')
        WIDGET_CONTROL, main_base, SENSITIVE=0
        WIDGET_CONTROL, popupbase, /REALIZE
        WIDGET_CONTROL,popupdraw1 , GET_VALUE=drawid1
        WIDGET_CONTROL,popupdraw2 , GET_VALUE=drawid2
        WIDGET_CONTROL,popupdraw3 , GET_VALUE=drawid3,timer=0.0
        d=get_demod_cofe(path=path,back_num=backid)
        fi=d.file
         WIDGET_CONTROL, Popup_file, SET_VALUE = fi
         WSET, drawid1
         ERASE 
         plot,rebin(reform(d.data[chan,*,*]),256),/yn,/xs, background=0,color=5
         WSET, drawid2
         ERASE 
         plot,d.demod[chan,0,*],/yn,/xs, background=0,color=5
         WSET, drawid3
         ERASE 
         polmin=min(d.demod[chan,1:2,*])
         polmax=max(d.demod[chan,1:2,*])
         plot,d.demod[chan,1,*],/yn,/xs, yrange=[polmin,polmax],background=0,color=5
          oplot,d.demod[chan,2,*],color=55   
        XMANAGER, "Cofe_ground_test_b", popupbase, GROUP_LEADER=main_base, /NO_BLOCK
          END
      'GOBACK': BEGIN
                WIDGET_CONTROL, ev.top, /DESTROY

                ; Re-sensitize the main base
                WIDGET_CONTROL, main_base, SENSITIVE=1
           END
      'Get_File' : BEGIN 
         d=get_demod_cofe(path=path,back_num=backid)
         fi=d.file
         WIDGET_CONTROL, File_name, SET_VALUE = fi
         WIDGET_CONTROL, text_allsect, SET_VALUE = '.              All Revolutions Averaged'
         WIDGET_CONTROL, text_T, SET_VALUE ='.                        Temperature'
         WSET, allsectid 
         ERASE 
         plot,rebin(reform(d.data[chan,*,*]),256),/yn,/xs, background=0,color=5
         WSET, Tid 
         ERASE 
         plot,d.demod[chan,0,*],/yn,/xs, background=0,color=5
         WSET, Qid 
         ERASE 
         polmin=min(d.demod[chan,1:2,*])
         polmax=max(d.demod[chan,1:2,*])
         plot,d.demod[chan,1,*],/yn,/xs, yrange=[polmin,polmax],background=0,color=5
          oplot,d.demod[chan,2,*],color=55
         End
         
         'NPS' : BEGIN 
         df=cofe_get_current_file(path=path, back_num=back_num)
         fi=strmid(df,20,/reverse)
         WIDGET_CONTROL, File_name, SET_VALUE = fi
         get_cofe_daq_x,d,files=df,/dontfix
         num=n_elements(d.data[0,0,*])
         c=reform(reform(d.data[chan,*,*],1,256.0*num))
         z=npsnoplot(c,256.0*30.0,1)
         WIDGET_CONTROL, text_allsect, SET_VALUE = '                 Normalized Power Spectrum'
         WSET, allsectid 
         ERASE 
         plot_io,z[*,0],z[*,1],/yn,/xs, background=0,color=5
         End
         
         'ONPS' : BEGIN 
         df=cofe_get_current_file(path=path, back_num=back_num)
         fi=strmid(df,20,/reverse)
         WIDGET_CONTROL, File_name, SET_VALUE = fi
         get_cofe_daq_x,d,files=df,/dontfix
         num=n_elements(d.data[0,0,*])
         c=reform(reform(d.data[chan,*,*],1,256.0*num))
         WSET, allsectid
         z=onps(c,256.0*30.0,1)
         End
         
       'Binned': Begin
         df=cofe_get_current_file(path=path, back_num=backid)
         get_cofe_daq_x,d,files=df,/dontfix
         fi=strmid(df,20,/reverse)
         WIDGET_CONTROL, text_allsect, SET_VALUE = '.              All Revolutions Averaged'
         WIDGET_CONTROL, text_T, SET_VALUE = '.              All Revolutions Sector 64'
         WIDGET_CONTROL, File_name, SET_VALUE = fi
         WSET, allsectid 
         ERASE 
         plot,rebin(reform(d.data[chan,*,*]),256),/yn,/xs, background=0,color=5
         WSET, Tid 
         ERASE 
         plot,d.data[chan,64,*],/yn,/xs, background=0,color=5
         
         End
            
        'STM': Begin
         temp_fi=strcompress(path+strmid(fi,12,13,/reverse),/remove_all)
         print,fi,'   ', temp_fi
         get_cofe_daq_x,d,files=temp_fi,/dontfix
         savetomain,d,Test_data
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
         'contin' : Begin
          WIDGET_CONTROL, ev.id, GET_VALUE = newname
          cont= float(newname)
         END   
      'done' : WIDGET_CONTROL, ev.top, /DESTROY 
   ENDCASE 
 endelse
END 
 
PRO Cofe_Ground_Test_b, Dir_date=Dir_date,GROUP=GROUP,pre_path=pre_path, platform=platform

  COMMON wDraw_share2, main_base,allsectid, Tid, Qid, maxid, chan, path, File_name, backid,text_allsect, $
      drawid1, drawid2, drawid3, popup_file, text_T, fi
  loadbwct
   if not(keyword_set(Dir_date)) then begin
      caldat,SYSTIME(/JULIAN, /UTC), month, day, year
      month=strcompress(string(month),/remove)
      year=strcompress(string(year),/remove)
      day=strcompress(strmid(systime(),8,2),/remove)
      if strlen(day) eq 1 then day=strcompress('0'+day,/remove)
      if strlen(month) eq 1 then month=strcompress('0'+month,/remove)
      Dir_date=strcompress(year+month+day,/remove)   
    endif
    
    if not(keyword_set(pre_path)) then pre_path=Cofe_get_file_path(platform=platform)
    
    path=pre_path+strcompress(Dir_date,/remove_all)
    result=file_info(path)
    if not(result.exists) then path =pre_path+'20100528'
    fi=path
   main_base = WIDGET_BASE(/ROW,Title='Cofe Data Analysis', XSIZE=800, YSIZE=800) 
   column1=widget_base(main_base,/column)
   text_allsect=widget_text(column1,value='.              All Revolutions Averaged' , UVALUE = 'test_allsect')
   draw_allsect = WIDGET_DRAW(column1, XSIZE=500, YSIZE=200) 
   
   text_T=widget_text(column1,value='.                        Temperature', UVALUE='text_T')
   draw_T = WIDGET_DRAW(column1, XSIZE=500, YSIZE=200) 
   text_Q=widget_text(column1,value='.                     Q (red) and U (blue)')
   draw_Q = WIDGET_DRAW(column1, XSIZE=500, YSIZE=200) 
   Current_path=widget_text(column1,value=path, UVALUE = 'Current_Path')
   button_base = WIDGET_BASE(main_base, /COLUMN) 
   buttongf = WIDGET_BUTTON(button_base, VALUE='Get File', UVALUE='Get_File') 
      
   buttonnps = WIDGET_BUTTON(button_base, VALUE='NPS', UVALUE='NPS')
   buttononps = WIDGET_BUTTON(button_base, VALUE='ONPS', UVALUE='ONPS')
   popup = WIDGET_BUTTON(button_base, VALUE='Continuous', UVALUE='popup')
   
   buttonbinned = widget_button(button_base, VALUE='Binned', UVALUE='Binned') 
   buttonSTM = WIDGET_BUTTON(button_base, VALUE='Save to Main', UVALUE='STM')
      
   button = widget_button(button_base, VALUE='Done', UVALUE='done') 
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
       
   Title_file_name=widget_text(column3,value='File Name',xsize=25)
   File_name=widget_text(column3,uvalue='File_name')
   
   drawid1=1.0
   drawid2=2.0
   drawid3=3.0
   WIDGET_CONTROL, main_base, /REALIZE 
   
   WIDGET_CONTROL, draw_allsect, GET_VALUE=allsectid
   WIDGET_CONTROL, draw_T, GET_VALUE=Tid
   WIDGET_CONTROL, draw_Q, GET_VALUE=Qid
   WIDGET_CONTROL, channel, GET_VALUE=chan
   WIDGET_CONTROL, Max_phase, GET_VALUE=maxid
   WIDGET_CONTROL, back, GET_VALUE=backid
   WIDGET_CONTROL, main_base, SET_UVALUE=allsectid
   
   
   
   XMANAGER, 'Cofe_ground_test_b', main_base, GROUP_LEADER=GROUP,/NO_BLOCK 
   
END 