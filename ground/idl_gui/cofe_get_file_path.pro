function Cofe_get_file_path,platform=platform
if not(keyword_set(platform)) then platform='mac
case platform of

'mac': search_string='/'

'pc':search_string='\'

endcase

c=pickfile(title='Pick Any file in the path you want')

string_path_len=strpos(c,search_string, /reverse_search)

string_path=strmid(c,0,string_path_len)

string_path=strcompress(string_path+search_string,/remove_all)
return, string_path

end