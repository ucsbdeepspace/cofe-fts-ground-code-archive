function Cofe_get_current_file, path=path, back_num=back_num

If not(keyword_set(path)) then path='/Users/brianw/Cofe/Test_data/20100528'
    
    If not(keyword_set(back_num)) then back_num=0
         crap=file_search(path+'/*.dat')
         dd=sort(crap)
         ddd=crap[dd]
         df=ddd[n_elements(ddd)-(back_num+1)]
         result=file_info(df)
         if result.size lt 1000.0 then df=ddd[n_elements(ddd)-(back_num+2)]
        
return, df

end
