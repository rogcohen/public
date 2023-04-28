# -*- coding: ISO-8859-1 -*-
import unicodedata
import string
import re
from os.path import exists



hash_dict = {"e":2,"t":3,"a":5,"o":7,"i":11,"n":13,"s":17,"h":19,"r":23,"d":29,"l":31,"u":37,"b":41,"c":43,"f":47,"g":53,"j":59,"k":61,"m":67,"p":71,"q":73,"v":79,"w":83,"x":89,"y":97,"z":101}

file_suffix = "_only.dat"

delete_dict = {sp_character: '' for sp_character in string.punctuation}
delete_dict[' '] = ''
delete_dict['ø'] = 'o'

delete_table = str.maketrans(delete_dict)

file_dict = {}
output_dict = {}



def hash_string(s):
  t = 1
  for l in s:
    t *= hash_dict[l]
  return t

def strip_accents(text):
    try:
        text = unicode(text, 'ISO-8859-1')
    except NameError: # unicode is a default on python 3 
        pass
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("ISO-8859-1")
    return str(text)

#with open("ukacd17.txt","r") as f:
#  l = f.readline().strip()
#  start = strip_accents(l[0].lower())
#  o = open(start + "_only.txt","w")
#  while l:
#    if strip_accents(l[0].lower()) != start:
#      start = strip_accents(l[0].lower())
#      o.close()
#      o = open(start + "_only.txt","w")
#    o.write(l + "\n")
#    #print(l.lower().strip())
#    #print(l[0])
#    l = f.readline().lower().strip()


def split_file(fname,file_dict,output_dict):
  with open(fname,"r") as f:
    l = f.readline().strip()
    while l:
      l_lookup = strip_accents(l.translate(delete_table).lower())
#      n = re.findall(r"[^a-z\ ]",l)
#      if n:
#        if 'ø' in l:
#          print(l,l_lookup)
#        if len(l_lookup) != len(re.sub( r"[\ " + "\\".join(list(string.punctuation)) + r"]","",l)):
#          nonascii.append(l)
      
      length = len(l_lookup)
      if length not in output_dict.keys():
        output_dict[length] = {}
      use_line = l_lookup not in output_dict[length].keys()
      if use_line:
        output_dict[length][l_lookup] = [l,str(hash_string(l_lookup))]
      l = f.readline().strip()

def write_dict_to_files(output_dict):
  file_dict = {}
  for l in output_dict.keys():
    if l not in file_dict.keys():
      file_name = str(l) + file_suffix
      file_dict[l] = open(file_name,"w")
    for x in output_dict[l].keys():
      line = x + '|' + output_dict[l][x][0] + '|' + output_dict[l][x][1] + "\n"
#      print(line)
      file_dict[l].write(line)  

#        if prefix not in file_dict.keys():
#          file_dict[prefix] = open(file_name,"w")
#        #line = '"' + l_lookup + '":["' + l + '",' + str(hash_string(l_lookup)) + "]"
#        line = l_lookup + '|' + l + '|' + str(hash_string(l_lookup))
#      l = f.readline().strip()
#      if l and use_line:
#        line = line + "\n"
#        file_dict[prefix].write(line)  
#

    
    
#        prefix = len(l_lookup)
#        file_name = str(prefix) + file_suffix
#        if prefix not in file_dict.keys():
#          file_dict[prefix] = open(file_name,"w")
#        #line = '"' + l_lookup + '":["' + l + '",' + str(hash_string(l_lookup)) + "]"
#        line = l_lookup + '|' + l + '|' + str(hash_string(l_lookup))
#      l = f.readline().strip()
#      if l and use_line:
#        line = line + "\n"
#        file_dict[prefix].write(line)  
#
  

#nonascii1 = []
#nonascii2 = []

#nonascii1 = nonascii1 + split_file("UKACD17.TXT",file_dict,output_dict,nonascii1)
#nonascii2 = nonascii2 + split_file("ENABLE.txt",file_dict,output_dict,nonascii2)
#print(nonascii1,nonascii2)

split_file("UKACD17.TXT",file_dict,output_dict)
split_file("ENABLE.txt",file_dict,output_dict)

sorted_dict = {}
for k in output_dict.keys():
  sorted_dict[k] = dict(sorted(output_dict[k].items()))

write_dict_to_files(sorted_dict)

#