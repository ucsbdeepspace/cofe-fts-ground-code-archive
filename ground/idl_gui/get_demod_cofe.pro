function Get_Demod_cofe, path=path, back_num=back_num

    If not(keyword_set(path)) then path='/Users/brianw/Cofe/Test_data/20100528'
    
    If not(keyword_set(back_num)) then back_num=0
    
          df=cofe_get_current_file(path=path, back_num=back_num)
         
         get_cofe_daq_x,d,files=df,/dontfix
         ddemod=c_demod(d,phase=maxid)
         fi=strmid(df,20,/reverse)
       

outstruct=create_struct('data',d.data,'demod',ddemod.demod,'file',fi)
return, outstruct

end