# -*- coding: ISO-8859-1 -*-
#import codecs

#After Simon Long <kudata@btinternet.com>

import unicodedata
import re
import itertools
import collections
import time
import string
import numpy
import pprint

from os import environ
from math import comb
from functools import (reduce, partial)
#from functools import partial

import kivy
from kivy.utils import escape_markup
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.effects.scroll import ScrollEffect
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen


from kivy.properties import (
    NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty, ListProperty
)
debug_android = False

class utils:
  def is_android(self):
    return 'ANDROID_BOOTLOGO' in environ

#  def call_chambers_dic(text):
#    Intent = autoclass('android.content.Intent')
#    Uri = autoclass('android.net.Uri')
#Intents = autoclass("android.provider.ContactsContract$Intents")
#Insert = autoclass("android.provider.ContactsContract$Intents$Insert")
#ContactsContract = autoclass("android.provider.ContactsContract")
#Contacts = autoclass("android.provider.ContactsContract$Contacts")


  #chamdic://

class solver:
  max_length = 30
  command_history =[]
  master_dict = {}
  file_list = ["UKACD17.TXT","ENABLE.txt"]

  master_control = {}
  master_control["split"]                 = [":","Separates length section of the command from the match and anagram section",""]
  master_control["anagram"]               = ["/","Anagram string: the following letters must occur in the returned words. If the anagram string is longer than the length of the returned words, then all anagrams that can be formed from those letters will be returned","/stop finds opts,post,pots,spot,stop,tops,"]
  master_control["misprint"]              = ["'","Misprint marker: return words matching a pattern with as many letters misprinted as ' symbols in the command","'besides finds besides,betides,resides"]
  master_control["space"]                 = ["_","Use in the length section to specify one or more spaces","10-12__:fer! finds free on rail, free on board, fresh as paint"]
  master_control["one_character"]         = ["?","Any single character","a?en finds Aden, agen, amen"]
  master_control["any_characters"]        = ["!","One or more characters","5-9:yo!an finds youthen, young man"]
  master_control["length_separator"]      = ["-","Separates minimum and maximum lengths of required words","5-8:fred! finds all words beginning with 'fred' of lengths 5,6,7,and 8 characters"]
  master_control["open_bracket"]          = ["(","() encloses any one of a list of letters","sho(pde) finds shod, shoe, shop"]
  master_control["close_bracket"]         = [")","() encloses any one of a list of letters","sho(pde) finds shod, shoe, shop"]
  master_control["open_neg_bracket"]      = ["[","[] encloses any one of a list of letters that must not occur","sho[pde] finds shog, shoo, shot, show"]
  master_control["close_neg_bracket"]     = ["]","[] encloses any one of a list of letters that must not occur","sho[pde] finds shog, shoo, shot, show"]
  master_control["vowel"]                 = ["@","Any vowel","sho@ finds shoe, shoo"]
  master_control["consonant"]             = ["&","Any consonant","sho& finds shod, shog, shop, shot, show"]
  master_control["expand_to_length"]      = ["~","Find all words of the given length that include thhe letters of the string in the given order (equivalent to inserting '!' between each character)","6:~fruy finds frouzy, fruity, frumpy"]
  master_control["find_anagram"]          = ["^","Find anagrams of the given length formed from jumbles of consecutive letters. Only one length may be specified","7:^ilovecrosswords finds escrows, sorrows"]
  master_control["anagram_group"]         = [",","Within an anagram letter string, the preceeding letters must occur togther (in any order)","8:/trib,und finds underbit but not turbined, unturbid"]
  master_control["anagram_group_ordered"] = [";","Within an anagram letter string, the preceeding letters must occur togther in the given order","8:not,zi finds notarize, zoonotic but not entozoic, schizont"]
  master_control["two_word_match"]        = ["+","Two words in which the numbered variables match but every variable represents a different letter","b12r=fl1d finds bear,fled"]
  master_control["two_word_match_repeat"] = ["=","Two words in which the numbered variables match and variables may represent the same letter","b12r=fl1d finds bear,fled and beer,fled"]
  master_control["test_all_rots"]         = ["%","Try every possible Caeser cipher and return all that make real words","%ibm finds lep,ohs,pit,ate,Hal"]
  master_control["only_uppercase"]        = ["$","Return only words starting with an uppercase letter; only valid as the first character","$aron finds Aaron and not baron"]

  control_chars = {str(x[0]):str(x[1][0]) for x in master_control.items()}
  valid_prefix_chars = re.escape(control_chars["only_uppercase"])

  error_messages = {}
  error_messages["malformed"] = "String is malformed"
  error_messages["too_many_colons"] = "String contains more than one colon (':')"
  error_messages["bad_characters"] = "String contains forbidden characters"
  error_messages["bad_pattern"] = "Illegal pattern"
  error_messages["bad_length"] = "Length section malformed"
  error_messages["bad_brackets"] = "Erroneous bracketing, or forbidden characters inside brackets"
  error_messages["expand_to_length_bad_length"] = "Only a single length may be specified"
  error_messages["bad_anagram_group"] = "Error in placement of anagram group marker"
  error_messages["bad_anagram_characters"] = "Forbidden characters used in anagram section"
  error_messages["bad_two_word_match"] = "Malformed two word match request"
  error_messages["bad_test_all_rots"] = "Malformed test all alphabet rotations request. Specify only 0 or 1 length"
  error_messages["duplicate_item_in_control_char_dict"] = "Duplicate control character"
  error_messages["prefix_characters_only_in_prefix"] = "Prefix characters (" + valid_prefix_chars + ") may only occur before all other characters"

  valid_lengths_chars = "0-9" + control_chars["length_separator"] + control_chars["space"]
  valid_pattern_chars = "a-zA-Z0-9" + control_chars["anagram"] + control_chars["any_characters"] + \
    control_chars["misprint"] + re.escape(control_chars["open_bracket"]) + re.escape(control_chars["close_bracket"]) + \
    re.escape(control_chars["open_neg_bracket"]) + re.escape(control_chars["close_neg_bracket"]) + \
    re.escape(control_chars["one_character"]) + re.escape(control_chars["expand_to_length"]) + \
    re.escape(control_chars["find_anagram"]) + re.escape(control_chars["consonant"]) + re.escape(control_chars["vowel"]) + \
    re.escape(control_chars["find_anagram"]) + re.escape(control_chars["find_anagram"]) + \
    re.escape(control_chars["two_word_match"]) + re.escape(control_chars["two_word_match_repeat"]) + \
    re.escape(control_chars["test_all_rots"])

  valid_anagram_chars = "a-zA-Z" + control_chars["one_character"] + re.escape(control_chars["open_bracket"]) + \
    re.escape(control_chars["close_bracket"]) + re.escape(control_chars["consonant"]) + re.escape(control_chars["vowel"]) + \
    re.escape(control_chars["anagram_group"]) + re.escape(control_chars["anagram_group_ordered"]) + \
    re.escape(control_chars["open_neg_bracket"]) + re.escape(control_chars["close_neg_bracket"])

  def insert_between_all_characters(self,s,char):
    return char + "".join([x + char for x in s])


  prefix_chars_regex = r"[" + insert_between_all_characters(None,valid_prefix_chars,"|").strip("|") + r"]"
  
  vowels_regex = r"[aeiou]"
  any_vowel_regex = r"[a|e|i|o|u]"
  any_consonant_regex = r"[^a|e|i|o|u|" + re.escape(control_chars["vowel"]) + r"|" + re.escape(control_chars["consonant"]) + r"|" + \
      re.escape(control_chars["one_character"]) + r"]"

  consonants_regex = "[^aeiou]"
  vowels = "aeiou"
  consonants = "bcdfghjklmnpqrstvwxyz"

  d_vc_replacement = {}
  d_vc_replacement[control_chars["vowel"]] = any_vowel_regex
  d_vc_replacement[control_chars["consonant"]] = any_consonant_regex
  d_vc_replacement[control_chars["one_character"]] = "."
  
  hash_dict = {"e":2,"t":3,"a":5,"o":7,"i":11,"n":13,"s":17,"h":19,"r":23,"d":29,"l":31,"u":37,"b":41,"c":43,"f":47,"g":53,"j":59,"k":61,"m":67,"p":71,"q":73,"v":79,"w":83,"x":89,"y":97,"z":101}
  file_suffix = "_only.dat"
  file_data_separator = "|"
  two_word_match_separator = ";"

  delete_dict = {sp_character: '' for sp_character in string.punctuation}
  delete_dict[' '] = ''
  #Slashed o (ø) not recognized as literal on Android
  delete_dict[chr(248)] = 'o'
  delete_table = str.maketrans(delete_dict)


  anagram_max_hash = 60000

  def __init__(self):
    self.master_dict = self.read_all_data()
    #self.master_dict = self.read_all_data_from_single_files(self.file_list)
    
    if not self.check_control_dict(self.control_chars):
      print(self.error_messages["duplicate_item_in_control_char_dict"])
      exit()


  def check_control_dict(self,d):
    #def check_for_duplicate_keys(d):
    #print(d.values())
    #print(len(d.items()),len(set(d.items())))
    return len(d.values()) == len(set(d.values()))
    #def no_reserved_characters(d):
      

  def rot_any(self,s,rot):
    rot_table = dict(zip(string.ascii_lowercase, string.ascii_lowercase[rot:] + string.ascii_lowercase[:rot]))
    return "".join([rot_table.get(x,x) for x in s])

  def all_rots(self,s):
    return {x:self.rot_any(s,x) for x in range(26)}

  def num_combinations(self,anagram_string,length):
    bracketed_regions = self.get_all_par(anagram_string,self.control_chars["open_bracket"],self.control_chars["close_bracket"])
    bracketed_expand_count = reduce(lambda x,y: x*y,(len(z) for z in bracketed_regions),1)
    vowel_count = anagram_string.count(self.control_chars["vowel"])
    consonant_count = anagram_string.count(self.control_chars["consonant"])
    one_character_count = anagram_string.count(self.control_chars["one_character"])
    residual_length = self.real_length(anagram_string) - (vowel_count + consonant_count + one_character_count)
    return max(5**vowel_count,1) * max(21**consonant_count,1) *  max(26**one_character_count,1) * \
      max(bracketed_expand_count,1) * max(max(comb(residual_length,length),residual_length),1)

  def par_regex(self,open_par,close_par):
    return re.compile(re.escape(open_par) + "([^" + re.escape(close_par) + "]+)" + re.escape(close_par))

  def get_all_par(self,s,open_par,close_par):
    #print(self.par_regex(open_par,close_par),re.findall(self.par_regex(open_par,close_par),s))
    return re.findall(self.par_regex(open_par,close_par),s)

  def valid_chars(self):
    return  "a-zA-Z0-9" + "".join([re.escape(x) for x in self.control_chars.values()])

  def read_data(self,length):
  	d = {}
  	try:
  		with open(str(length) + self.file_suffix,encoding="iso-8859-1") as f:
  			d = {s[0]:[s[1],int(s[2])] for s in [x.split(self.file_data_separator) for x in f.read().split("\n") if x]}
  	except FileNotFoundError:
  		pass
  	return d

  def read_all_data(self):
    return {l: self.read_data(l) for l in range(1,self.max_length)}

  def split_file(self,fname,output_dict):
    def strip_accents(text):
      try:
        text = unicode(text, 'ISO-8859-1')
      except NameError: # unicode is a default on python 3 
        pass
      text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("ISO-8859-1")
      return str(text)
    
    with open(fname,"r") as f:
      l = f.readline().strip()
      while l:
        l_lookup = strip_accents(l.translate(self.delete_table).lower())
        length = len(l_lookup)
        if length not in output_dict.keys():
          output_dict[length] = {}
        use_line = l_lookup not in output_dict[length].keys()
        if use_line:
          output_dict[length][l_lookup] = [l,self.hash_string(l_lookup)]
        l = f.readline().strip()

  def read_all_data_from_single_files(self,file_list):
    output_dict = {}
    for f in file_list:
      self.split_file(f,output_dict)
    return output_dict


#  def read_all_data_from_single_file(self):
#    output_dict = {}
#    self.split_file("UKACD17.TXT",output_dict)
#    self.split_file("ENABLE.txt",output_dict)
#    return output_dict

#  def hash_string(self,s):
#    t = 1
#    for l in s:
#      t *= self.hash_dict[l]
#    return t

  def hash_string(self,s):
    return reduce(lambda x,y: x*y, (self.hash_dict[z] for z in s),1)

#  def lookup_by_hash(self,d,v):
#    return list(filter(lambda l: l[1] == v, d.values()))

#  def get_anagrams_from_dict1(self,s,l):
#    return self.lookup_by_hash(self.master_dict[l],self.hash_string(s))

#  def get_anagrams_from_dict2(self,s,d):
#    return dict(filter(lambda l: l[1][1] == self.hash_string(s), d.items()))

#  def get_partial_anagrams_from_dict(self,s,d):
#    return dict(filter(lambda l: l[1][1]%self.hash_string(s) == 0, d.items()))
      
  def anagram_group_list(self,split_char,group_string):
    if split_char == self.control_chars["anagram_group_ordered"]:
      result = [group_string]
    elif split_char == self.control_chars["anagram_group"]:
      result = ["".join(x) for x in set(list(itertools.permutations(group_string)))]
    return result

  def filter_match_list(self,d,match_list):
    result = {}
    for x in match_list:
      result = result | self.filter_dict(self.control_chars["any_characters"] + x + self.control_chars["any_characters"],d)
    return result

#    result = {}
#    if split_char == self.control_chars["anagram_group_ordered"]:
#      result = self.filter_dict(self.control_chars["any_characters"] + group_string + self.control_chars["any_characters"],d)
#    elif split_char == self.control_chars["anagram_group"]:
#      match_list = list(set(list(itertools.permutations(group_string))))
#      for x in match_list:
#        result = result | self.filter_dict(self.control_chars["any_characters"] + "".join(x) + self.control_chars["any_characters"],d)
#    return result
  def exist_bracketed_regions(self,s):
    return ((s.count(self.control_chars["open_bracket"]) != 0) or (s.count(self.control_chars["open_neg_bracket"]) != 0))

  def get_all_partial_anagrams(self,anagram_string,split_char,group_string,d):
    result = {}
    anagram_string = anagram_string.replace(self.control_chars["one_character"],"")
    exist_bracketed_regions = self.exist_bracketed_regions(anagram_string)
    exist_consonant_marker = anagram_string.count(self.control_chars["consonant"]) != 0
    exist_vowel_marker = anagram_string.count(self.control_chars["vowel"]) != 0 

    anagram_string_no_brackets = self.remove_non_alpha(self.remove_bracketed_regions(anagram_string))
    if len(anagram_string_no_brackets) > 0:
      d = dict(filter(lambda l: l[1][1]%self.hash_string(anagram_string_no_brackets) == 0, d.items()))
    
    if not exist_consonant_marker and not exist_vowel_marker and not exist_bracketed_regions:
      new_anagram_string_list = [anagram_string]
    else:
      new_anagram_string_list = set()
      if exist_bracketed_regions:
        new_anagram_string_list = self.expand_character_choice(anagram_string,"",set())
      else:
        new_anagram_string_list = [anagram_string]
      for x in anagram_string_list:
        new_anagram_string_list = new_anagram_string_list | self.expand_vowel_and_consonants1(x,set())
#    print(new_anagram_string_list)
#    for a in new_anagram_string_list:
#      result = result | dict(filter(lambda l: l[1][1]%self.hash_string(a) == 0, d.items()))
    hash_list = numpy.array([self.hash_string(x) for x in set(new_anagram_string_list)])
    result = dict(filter(lambda l: not numpy.all(l[1][1]%hash_list), d.items()))
    return result


  def filter_dict(self,filter_expression,d,remove_number_var_duplicates = True):
    regex = self.charstring_to_regex(filter_expression)
    r = re.compile(regex)
    d = {k:v for (k,v) in d.items() if r.match(k)}
    if ((regex.count("(") != 0) and (remove_number_var_duplicates)): 
      d = dict(filter(lambda x: len(re.findall(regex,x[0])[0]) == len(set(re.findall(regex,x[0])[0])), d.items()))
    return d

  def filter_char(self,char,d,c):
    return {k:v for (k,v) in d.items() if k.count(char) >= c}

  def filter_spaces(self,spaces,d):
    return dict(filter(lambda l: l[1][0].count(" ") == spaces, d.items()))

  def filter_uppercase(self,d):
    return dict(filter(lambda l: l[1][0][0].isupper(), d.items()))

  def check_valid_chars(self,s):
    regex = r"[^a-zA-Z]"
    result = False
    for x in s:
      result = re.search(regex,x)
      if result:
        break
    return not result

  def number_variables(self,char_string):
    result = char_string
    replace_dict = {}
    replace_number = 1
    numbers = re.findall(r"[0-9]",char_string)
    for x in numbers:
      if x not in replace_dict.keys():
        replace_dict[x] = "\\\\" + str(replace_number)
#        replace_number = replace_number + 1
        replace_number += 1
    for x in replace_dict.keys():
      result = result.replace(x,"(.)",1)
    for x in replace_dict.items():
      #"(?<!\\\\)" is a negative look behind assertion: numbers must not be preceeded by "\"
      regex = re.compile("(?<!\\\\)" + x[0])
      result = re.sub(regex,x[1],result)
    return result

  def strip_prefix_chars(self,s):
    return re.sub(r"^" + self.prefix_chars_regex + r"*","",s)

  def get_prefix_chars(self,s):
    return re.search(self.prefix_chars_regex + r"*",s).group()
  

  def validate_length_string(self,length_string):
    error_message = ""
    regex2 = r"[^" + self.valid_lengths_chars + r"]"
    regex_numbers = r"[^0-9" + self.control_chars["space"] + r"]"
    result = not re.search(regex2,length_string)
    if result:
      l = length_string.split(self.control_chars["length_separator"])
      result = not len(l) >= 3
    if result:
      result = not re.search(regex_numbers,l[0])
    if result:
      space_marker_no = length_string.count(self.control_chars["space"])
      result = ((space_marker_no == 0) or \
                  (space_marker_no > 0 and len(l) == 1) or \
                  (space_marker_no > 0 and len(l) == 2 and l[1].count(self.control_chars["space"]) == space_marker_no))
    if result and space_marker_no > 0:
      result = length_string.rstrip(self.control_chars["space"]) ==  length_string[: len(length_string) - space_marker_no]
    if result and len(l) == 2:
      result = not re.search(regex_numbers,l[1])
      if result:
        result = int(l[1].rstrip(self.control_chars["space"])) > int(l[0])
    if not result:
      error_message = self.error_messages["bad_length"]
    return result,error_message

  def validate_char_string(self,char_and_anagram_string,length_string_exists,length_string):
    def valid_bracketed_regions(s):
      bracketed_regions = self.get_all_par(s,self.control_chars["open_bracket"],self.control_chars["close_bracket"]) + \
           self.get_all_par(s,self.control_chars["open_neg_bracket"],self.control_chars["close_neg_bracket"])
      open_brackets = s.count(self.control_chars["open_bracket"]) + s.count(self.control_chars["open_neg_bracket"])
      close_brackets = s.count(self.control_chars["close_bracket"]) + s.count(self.control_chars["close_neg_bracket"])
      num_bracketed_regions = len(bracketed_regions)
      valid = ((num_bracketed_regions == open_brackets) and (num_bracketed_regions == close_brackets))
      if num_bracketed_regions > 0 and valid:
        valid = self.check_valid_chars(bracketed_regions)
      return valid
    
    regex3 = r"[^" + self.valid_pattern_chars + r"]"
    anagram_regex = r"[^" + self.valid_anagram_chars + r"]"
    error_message = ""
    anagram_marker_no = char_and_anagram_string.count(self.control_chars["anagram"])
    misprint_marker_no = char_and_anagram_string.count(self.control_chars["misprint"])
    expand_to_length_marker_no = char_and_anagram_string.count(self.control_chars["expand_to_length"])
    find_anagram_count = char_and_anagram_string.count(self.control_chars["find_anagram"])
    anagram_group_count = char_and_anagram_string.count(self.control_chars["anagram_group"])
    anagram_group_ordered_count = char_and_anagram_string.count(self.control_chars["anagram_group_ordered"])
    test_all_rots_count = char_and_anagram_string.count(self.control_chars["test_all_rots"])

    two_word_match_count = char_and_anagram_string.count(self.control_chars["two_word_match"])
    two_word_match_repeat_count = char_and_anagram_string.count(self.control_chars["two_word_match_repeat"])
    
    no_brackets = not self.exist_bracketed_regions(char_and_anagram_string)
    result = find_anagram_count <= 1
    
    if result and find_anagram_count == 1:
      result = (char_and_anagram_string == self.control_chars["find_anagram"] + self.remove_non_alpha(char_and_anagram_string)) and \
          length_string_exists and length_string.count(self.control_chars["length_separator"]) == 0
    if not result:
      error_message = "1: " + self.error_messages["bad_characters"]
    
    result = result and anagram_marker_no <= 1
    if not result:
      error_message = "11: " + self.error_messages["bad_pattern"]
    if result and anagram_marker_no == 1:
      char_string,anagram_string = char_and_anagram_string.split(self.control_chars["anagram"])
      result = valid_bracketed_regions(anagram_string)
      if not result:
        error_message = "2: " + self.error_messages["bad_pattern"]
      if result:
        result = not re.search(anagram_regex,anagram_string)
        if not result:
          error_message = "3: " + self.error_messages["bad_anagram_characters"]
      if result and (anagram_group_ordered_count != 0 or anagram_group_count != 0):
        error_message = "4: " + self.error_messages["bad_anagram_characters"]
        result = (anagram_string.count(self.control_chars["anagram_group"]) + \
           anagram_string.count(self.control_chars["anagram_group_ordered"]) == 1) and \
           (anagram_group_count + anagram_group_ordered_count == 1)
        if not result:
          error_message = "5: " + self.error_messages["bad_anagram_group"]
      
    else:
      char_string = char_and_anagram_string
      anagram_string = ""
    if result:
      result = not re.search(regex3,char_string)
      if not result:
        error_message = "6: " + self.error_messages["bad_pattern"]
        
    if result:
      result = expand_to_length_marker_no <= 1
      if result and expand_to_length_marker_no == 1:
        result = char_string[0] == self.control_chars["expand_to_length"] and length_string_exists and anagram_string == "" and \
            two_word_match_count == 0 and \
            anagram_group_ordered_count == 0
#            length_string.count(self.control_chars["length_separator"]) == 0 and \
      if not result:
        error_message = "7: " + self.error_messages["expand_to_length_bad_length"]

    if result:
      result = test_all_rots_count <= 1
      if result and test_all_rots_count == 1:
        result = char_string[0] == self.control_chars["test_all_rots"] and anagram_string == "" and \
            length_string.count(self.control_chars["length_separator"]) == 0 and two_word_match_count == 0
      if not result:
        error_message = "12: " + self.error_messages["bad_test_all_rots"]

    if result and ((two_word_match_count != 0) or (two_word_match_repeat_count != 0)):
      result = (two_word_match_count + two_word_match_repeat_count == 1) and (anagram_string == "" ) and (misprint_marker_no == 0) and \
      (expand_to_length_marker_no == 0) and (find_anagram_count == 0) and (not length_string_exists) and no_brackets and \
      test_all_rots_count == 0
      if not result:
        error_message = "8: " + self.error_messages["bad_two_word_match"]
    if result:
      result = ((misprint_marker_no == 0) or (anagram_marker_no == 0))
      if result and misprint_marker_no > 0:
        result = ((char_string.lstrip(self.control_chars["misprint"]) == char_string[misprint_marker_no :]) and \
          (not length_string_exists)) and no_brackets
      if not result:
        error_message = "9: " + self.error_messages["bad_characters"]
    if result:
      result = valid_bracketed_regions(char_string)
      if not result:
        error_message = "10: " + self.error_messages["bad_brackets"]
    return result,error_message

 
  def valid_command1(self,command_line):
    #t = ""
    error_message = ""
    regex1 = r"[^" + self.valid_chars() + r"]"
    #regex_chars = r"[^a-zA-Z]"
    result = (command_line != "") and not re.search(regex1,command_line)
    if result:
      command_line = self.strip_prefix_chars(command_line)
      result = not re.search(self.prefix_chars_regex,command_line) 
      if not result:
        error_message = self.error_messages["prefix_characters_only_in_prefix"]
    if result:
      clist = command_line.split(self.control_chars["split"])
      result = not len(clist) >= 3
      if result:
        length_string_exists = len(clist) == 2
      else:
        error_message = self.error_messages["too_many_colons"]
    if result:
      char_string = clist[-1]
      if length_string_exists:
        result,error_message = self.validate_length_string(clist[0])
    if result:
      result,error_message = self.validate_char_string(char_string,len(clist) == 2,clist[0])
    return result,error_message

  def remove_bracketed_regions(self,s):
    b = re.sub(self.par_regex(self.control_chars["open_neg_bracket"],self.control_chars["close_neg_bracket"]),"",s)
    return re.sub(self.par_regex(self.control_chars["open_bracket"],self.control_chars["close_bracket"]),"",b)
    
  def remove_non_alpha(self,s):
    return re.sub(r"[^a-z]","",s)

  def real_length(self,s):
    s = s.replace(self.control_chars["anagram_group"],"")
    s = s.replace(self.control_chars["anagram_group_ordered"],"")
    b1 = self.get_all_par(s,self.control_chars["open_bracket"],self.control_chars["close_bracket"])
    b2 = self.get_all_par(s,self.control_chars["open_neg_bracket"],self.control_chars["close_neg_bracket"])
    s = self.remove_bracketed_regions(s)
    return len(s) + len(b1) + len(b2)

  def parse_command(self,c):
    kwargs = {}
    char_string = ""
    anagram_string = ""
    #spaces = ""
    lengths_split = [0]
    lengths = []
    lengths_stripped = []
    lengths_min = 0
    lengths_max = 0
    misprint_number = 0
    two_word_match_char = ""
#    control_chars["expand_to_length"]
    expand_to_length = False
    find_anagram = False
    test_all_rots = False
    only_uppercase = False
    valid,error_message = self.valid_command1(c)

    if valid:
      self.command_history.append(c)
      prefix_chars = self.get_prefix_chars(c)
      if prefix_chars != "":
        c = self.strip_prefix_chars(c)
        only_uppercase = self.control_chars["only_uppercase"] in prefix_chars
      clist = c.split(self.control_chars["split"])
      after_split = clist[-1]
      if after_split.count(self.control_chars["anagram"]) == 1:
        char_string,anagram_string = after_split.split(self.control_chars["anagram"])
      else:
        char_string = after_split
      misprint_number = char_string.count(self.control_chars["misprint"])
      if misprint_number >= 1:
        char_string = char_string.lstrip(self.control_chars["misprint"])
      find_anagram = char_string.count(self.control_chars["find_anagram"]) == 1
      char_string = char_string.lstrip(self.control_chars["find_anagram"])
      expand_to_length = char_string.count(self.control_chars["expand_to_length"]) == 1
      char_string = char_string.lstrip(self.control_chars["expand_to_length"])
      two_word_match = char_string.count(self.control_chars["two_word_match"]) == 1
      two_word_match_repeat = char_string.count(self.control_chars["two_word_match_repeat"]) == 1
      test_all_rots = char_string.count(self.control_chars["test_all_rots"]) == 1

      char_string = char_string.lstrip(self.control_chars["test_all_rots"])
      if two_word_match:
        two_word_match_char = self.control_chars["two_word_match"]
      elif two_word_match_repeat:
        two_word_match_char = self.control_chars["two_word_match_repeat"]
        
      
      if len(clist) == 2:
        lengths = clist[0]
        lengths_stripped = lengths.rstrip(self.control_chars["space"])
        #if lengths_stripped != lengths:
          #print(lengths_stripped)
          #print(lengths)
          #spaces = lengths[len(lengths_stripped) - len(lengths):len(lengths)]
        lengths_split = lengths_stripped.split(self.control_chars["length_separator"])
        lengths_min = min(int(lengths_split[0]),self.max_length - 1)
        lengths_max = min(int(lengths_split[-1]),self.max_length - 1)
      else:
        lengths_min = min(max(self.real_length(char_string),self.real_length(anagram_string)),self.max_length - 1)
        lengths_max = lengths_min
        if char_string.count(self.control_chars["any_characters"]) != 0:
          lengths_max = self.max_length - 1

    kwargs["lengths_min"]        = lengths_min        
    kwargs["lengths_max"]        = lengths_max        
    kwargs["char_string"]        = char_string.lower()        
    kwargs["anagram_string"]     = anagram_string.lower()     
    kwargs["misprint_number"]    = misprint_number    
    kwargs["spaces"]             = len(lengths) - len(lengths_stripped)             
    kwargs["find_anagram"]       = find_anagram       
    kwargs["expand_to_length"]   = expand_to_length   
    kwargs["two_word_match_char"]= two_word_match_char
    kwargs["test_all_rots"]      = test_all_rots
    kwargs["only_uppercase"]     = only_uppercase
    return kwargs,valid,error_message


  def charstring_to_regex(self,c):
    if c == "":
      r = ".*"
    else:
      r = c.replace(self.control_chars["one_character"],".")
      r = r.replace(self.control_chars["any_characters"],".*")
      r = r.replace(self.control_chars["open_neg_bracket"],"[^")
      r = r.replace(self.control_chars["open_bracket"],"[")
      r = r.replace(self.control_chars["close_bracket"],"]")
      r = r.replace(self.control_chars["close_neg_bracket"],"]")
      r = r.replace(self.control_chars["vowel"],self.vowels_regex)
      r = r.replace(self.control_chars["consonant"],self.consonants_regex)
      r = self.number_variables(r)
    return "^" + r + "$"

  def reconstruct_string(self,d):
    return "".join(x[0] * x[1] for x in d.items())

  def letter_difference(self,str_a,str_b):
    return self.reconstruct_string(collections.Counter(str_b) - collections.Counter(str_a))
    

  def get_all_anagrams1(self,anagram_string,split_char,group_string,d,length):
    def anagram_compare(anagram_string,test_string,counts,special_chars):
      d_anagram_string = collections.Counter(anagram_string)
      d_original_test_string = collections.Counter(test_string)
      d_test_string = d_original_test_string - d_anagram_string
      if len(d_test_string) > 0 and special_chars:
        for x in counts.keys():
          if counts[x] > 0:
            d_anagram_string = d_anagram_string - d_original_test_string
            test_string = re.sub(self.d_vc_replacement[x],x,self.reconstruct_string(d_test_string))
            d_original_test_string = collections.Counter(test_string)
            d_test_string =  d_original_test_string - d_anagram_string
            #print(test_string,d_test_string,d_anagram_string,d_original_test_string)
          if len(d_test_string) == 0:
            break
      return len(d_test_string) == 0
    result = {}
    if self.exist_bracketed_regions(anagram_string):
      anagram_string_list = self.expand_character_choice(anagram_string,"",set())
    else:
      anagram_string_list = [anagram_string]
    for a in anagram_string_list:
      if len(a) < length:
        working_anagram_string = a + self.control_chars["one_character"] * (length - len(a))
      else:
        working_anagram_string = a
      counts = {}
      counts[self.control_chars["consonant"]] = working_anagram_string.count(self.control_chars["consonant"])
      counts[self.control_chars["vowel"]] = working_anagram_string.count(self.control_chars["vowel"])
      counts[self.control_chars["one_character"]] = working_anagram_string.count(self.control_chars["one_character"])
      special_chars = sum(x[1] for x in counts.items()) > 0
      result = result | dict(filter(lambda l: anagram_compare(working_anagram_string,l[0],counts,special_chars),d.items()))
    return result

  def expand_vowel_and_consonants1(self,anagram_string,anagram_string_list):
    if anagram_string.count(self.control_chars["vowel"]) > 0:
      for x in self.vowels:
        new_anagram_string = anagram_string.replace(self.control_chars["vowel"],x,1)
        new_anagram_string = self.expand_vowel_and_consonants1(new_anagram_string,anagram_string_list)
    elif anagram_string.count(self.control_chars["consonant"]) > 0:
      for x in self.consonants:
        new_anagram_string = anagram_string.replace(self.control_chars["consonant"],x,1)
        new_anagram_string = self.expand_vowel_and_consonants1(new_anagram_string,anagram_string_list)
    elif anagram_string.count(self.control_chars["one_character"]) > 0:
      for x in string.ascii_lowercase:
        new_anagram_string = anagram_string.replace(self.control_chars["one_character"],x,1)
        new_anagram_string = self.expand_vowel_and_consonants1(new_anagram_string,anagram_string_list)
    else:
      anagram_string_list.add(anagram_string)
    return anagram_string_list

  def expand_character_choice(self,anagram_string,expanded_string,anagram_string_list):
    def build_strings(bracketed_regions,expanded_string,anagram_string_list,new_anagram_string):
      new_regions_list = bracketed_regions.copy()
      b = new_regions_list[0]
      del new_regions_list[0]
      for x in b:
        if len(new_regions_list) == 0:
          anagram_string_list.add(new_anagram_string + expanded_string + x)
        else:
          anagram_string_list = build_strings(new_regions_list,expanded_string + x,anagram_string_list,new_anagram_string)
      return anagram_string_list
    def convert_neg_to_positive(region_list):
      return ["".join(sorted(set(string.ascii_lowercase).difference(x))) for x in region_list]
    
    #bracketed_neg_regions = self.get_all_par(anagram_string,self.control_chars["open_neg_bracket"],self.control_chars["close_neg_bracket"])
    bracketed_regions = self.get_all_par(anagram_string,self.control_chars["open_bracket"],self.control_chars["close_bracket"]) + \
        convert_neg_to_positive(self.get_all_par(anagram_string,self.control_chars["open_neg_bracket"],self.control_chars["close_neg_bracket"]))
    new_anagram_string = re.sub(self.par_regex(self.control_chars["open_bracket"],self.control_chars["close_bracket"]),"",anagram_string)
    new_anagram_string = re.sub(self.par_regex(self.control_chars["open_neg_bracket"],self.control_chars["close_neg_bracket"]),"",new_anagram_string)
    anagram_string_list = build_strings(bracketed_regions,"",anagram_string_list,new_anagram_string)
    return anagram_string_list

  #When anagram string is longer than or equal to requested number of characters
  def get_all_anagrams(self,anagram_string,split_char,group_string,d,length):
#    t1 = time.perf_counter()
    exist_bracketed_regions = self.exist_bracketed_regions(anagram_string)
    exist_consonant_marker = anagram_string.count(self.control_chars["consonant"]) != 0
    exist_vowel_marker = anagram_string.count(self.control_chars["vowel"]) != 0 
    exist_one_character_marker = anagram_string.count(self.control_chars["one_character"]) != 0 

    if not exist_consonant_marker and not exist_vowel_marker and not exist_bracketed_regions and not exist_one_character_marker:
      hash_list = set([self.hash_string(x) for x in list(itertools.combinations(anagram_string,length))])
    else:
      hash_list = set()
      anagram_string_list = set()
      new_anagram_string_list = set()
      #t3 = time.perf_counter()
      if exist_bracketed_regions:
        anagram_string_list = self.expand_character_choice(anagram_string,"",set())
        #t4 = time.perf_counter()
      else:
        anagram_string_list = [anagram_string]
        #t5 = time.perf_counter()
      for x in anagram_string_list:
        new_anagram_string_list = new_anagram_string_list | self.expand_vowel_and_consonants1(x,set())
      #t6 = time.perf_counter()
        
#      t7 = time.perf_counter()
      #print(len(new_anagram_string_list) * comb(len(new_anagram_string_list[0]),length))
      for a in new_anagram_string_list:
        hash_list = hash_list | set([self.hash_string(x) for x in list(itertools.combinations(a,length))])
#      print(len(hash_list),len(set(hash_list)))
#      t8 = time.perf_counter()


#    print("t4 - t3",t4 - t3)
#    print("t6 - t5",t6 - t5)
#    print("t8 - t7",t8 - t7)
#    print("get_all_anagrams",len(hash_list),t2 - t1)
    #t1 = time.perf_counter()
    #test_hash_list = set([x[1][1] for x in d.items()])
    #intersect_list = list(test_hash_list & hash_list)
    #t2 = time.perf_counter()
    #print("get_all_anagrams",len(hash_list),t2 - t1)
    #t1 = time.perf_counter()
    #test1 = dict([x for x in d.items() if x[1][1] in hash_list])
    #t2 = time.perf_counter()
    #test2 = dict(filter(lambda l: l[1][1] in hash_list, d.items()))
    #t3 = time.perf_counter()
    #print("get_all_anagrams",len(hash_list),t2 - t1,t3 - t2)
    #return dict(filter(lambda l: l[1][1] in hash_list, d.items()))
    return dict([x for x in d.items() if x[1][1] in hash_list])
 
  def get_all_misprint_regex(self,result,num_to_replace,before,after,char_string):
    for x in range(len(after)):
      if after[x] not in "?*":
        before_new = before + after[:x].copy()
        after = char_string[-len(after):].copy()
        after[x] = "?"
        if num_to_replace == 1:
          result.append(before.copy() + after.copy())
        else:
          result = self.get_all_misprint_regex(result,num_to_replace - 1,before_new,after[x:].copy(),char_string)
    return result

  def get_misprints(self,char_string,misprint_number,d):
    result = {}
    all_misprint_regex = []
    c = list(char_string)
    all_misprint_regex = self.get_all_misprint_regex(all_misprint_regex,misprint_number,[],c,c)
    for x in all_misprint_regex:
      result = result | self.filter_dict("".join(x),d)
    return result

  def all_letters(self,s):
    return s.count(self.control_chars["open_bracket"]) == 0 and s.count(self.control_chars["open_neg_bracket"]) == 0 and \
        s.count(self.control_chars["consonant"]) == 0 and s.count(self.control_chars["vowel"]) == 0 and \
        s.count(self.control_chars["one_character"]) == 0
    
  def search_for_anagrams(self,char_string,length):
    d = {}
    for x in range(0,len(char_string) - length + 1):
      d = d | self.get_all_anagrams(char_string[x:x + length],"","",self.master_dict[length],length)
    return d

  def split_anagram_string(self,s):
    split_char = ""
    group_string = ""
    if s.count(self.control_chars["anagram_group"]):
      split_char = self.control_chars["anagram_group"]
    elif s.count(self.control_chars["anagram_group_ordered"]):
      split_char = self.control_chars["anagram_group_ordered"]
    if split_char != "":
      group_string,remainder = s.split(split_char)
      s = s.replace(split_char,"")
    return s,split_char,group_string

  def two_word_match(self,char_string,two_word_match_char):
    def letter_occurrences(s,letter):
      return [i for i,ch in enumerate(s) if ch == letter]
    
    def position_dict(s):
      d = {}
      numbers = re.findall(r"[0-9]",s)
      for x in set(numbers):
        d[x] = letter_occurrences(s,x)
      return d

    def make_regex(d,mutual_list,match_list,length):
      result = list(self.control_chars["one_character"] * length)
      c = 0
      for x in mutual_list:
        result[d[x][0]] = match_list[c]
        c += 1
      return "".join(result)

    result = []
    word1,word2 = char_string.split(two_word_match_char)
    word1_d = position_dict(word1)
    word2_d = position_dict(word2)
    mutual_list = list(word1_d.keys() & word2_d.keys())
    #print(mutual_list)
    # join_dict["abc"] = [[matching word list 1][matching word list 2]]
    join_dict = {}
    d1 = self.filter_dict(word1,self.master_dict[self.real_length(word1)],remove_number_var_duplicates = \
        (two_word_match_char == self.control_chars["two_word_match"]))
    d2 = self.filter_dict(word2,self.master_dict[self.real_length(word2)],remove_number_var_duplicates = \
        (two_word_match_char == self.control_chars["two_word_match"]))
    #start_time1 = time.perf_counter()

    for x1 in d1.keys():
      word1_char = []
      for m1 in mutual_list:
        word1_char.append(x1[word1_d[m1][0]])
      match_chars1 = "".join(word1_char)
      if ((two_word_match_char == self.control_chars["two_word_match_repeat"]) or (len(word1_char) == len(set(word1_char)))):
        if match_chars1 not in join_dict.keys():
          join_dict[match_chars1] = [set(),set()]
        join_dict[match_chars1][0].add(d1[x1][0])
        d3 = self.filter_dict(make_regex(word2_d,mutual_list,word1_char,self.real_length(word2)),d2)
        join_dict[match_chars1][1] = join_dict[match_chars1][1] | set(d3[x3][0] for x3 in  d3.keys())

#        for x3 in d3.keys():
#          join_dict[match_chars1][1].add(d3[x3][0])
    #end_time1 = time.perf_counter()
    #print("two_word_match1",end_time1 - start_time1)
#    result = [w1 + self.two_word_match_separator + w2 for w1,w2 in [y[1][0][0],y[1][1] for y in join_dict.items()]]
    for x in join_dict.items():
      for w1 in x[1][0]:
        for w2 in x[1][1]:
          result.append(w1 + self.two_word_match_separator + w2)
    return sorted(result,key = str.casefold)

  def find_all_rots(self,char_string,length):
    d = {}
    d2 = {}
    char_string_dict = self.all_rots(char_string)
    for rot_num in char_string_dict.keys():
      d1 = self.filter_dict(char_string_dict[rot_num],self.master_dict[length])
      for x in d1.keys():
        d2[x] = d1[x].copy()
        d2[x].append(str(rot_num))
        d = d | d2
    return list(d[y][0] + "(" + d[y][2] + ")" for y in d.keys()) 

  def find_included_words(self,char_string,length):
    if self.exist_bracketed_regions(char_string):
      string_list = self.expand_character_choice(char_string,"",set())
    else:
      string_list = list(char_string)
    pos_list = list(itertools.combinations(range(self.real_length(char_string)),length))
    d = {}
    for s in string_list:
      for l in pos_list:
        print(s,l)
        d = d | self.filter_dict("".join((s[c] for c in l)),self.master_dict[length])
    return d

  def insert_between_all_characters_par(self,s,char):
    def replace_func(s):
      return s.group(0).replace(char,"")
    open_bracket_regex = re.escape(self.control_chars["open_bracket"]) + "|" + re.escape(self.control_chars["open_neg_bracket"])
    close_bracket_regex = re.escape(self.control_chars["close_bracket"]) + "|" + re.escape(self.control_chars["close_neg_bracket"])
    return re.sub(r"([" +  open_bracket_regex + "][^" + close_bracket_regex + "]+[" + close_bracket_regex + "])", \
      replace_func,self.insert_between_all_characters(s,char))

  def main_action(self,**kwargs):
    lengths_min         = kwargs["lengths_min"]
    lengths_max         = kwargs["lengths_max"]
    char_string         = kwargs["char_string"]
    anagram_string      = kwargs["anagram_string"]
    misprint_number     = kwargs["misprint_number"]
    spaces              = kwargs["spaces"]
    find_anagram        = kwargs["find_anagram"]
    expand_to_length    = kwargs["expand_to_length"]
    two_word_match_char = kwargs["two_word_match_char"]
    test_all_rots       = kwargs["test_all_rots"]
    only_uppercase      = kwargs["only_uppercase"]
    results = []
    char_string_expanded = ""
    if anagram_string != "":
      anagram_string,split_char,group_string = self.split_anagram_string(anagram_string)
      real_length_anagram_string = self.real_length(anagram_string)
      if split_char != "":
        anagram_match_list = self.anagram_group_list(split_char,group_string)

#    if expand_to_length:
#      char_string = self.insert_between_all_characters(char_string,self.control_chars["any_characters"])
#      d = self.filter_dict(char_string,self.master_dict[lengths_max])
#      ret = list(d[x][0] for x in d.keys()) 
    if find_anagram:
      d = self.search_for_anagrams(char_string,lengths_max)
      sorted_dict = dict(sorted(d.items()))
      ret = list(sorted_dict[x][0] for x in sorted_dict.keys())
    elif two_word_match_char != "":
      ret = self.two_word_match(char_string,two_word_match_char)
    elif test_all_rots:
      ret = self.find_all_rots(char_string,lengths_max)
    else:
      for length in range(lengths_min,lengths_max + 1):
        d = {}
        if expand_to_length:
          if self.real_length(char_string) <= length:
            if char_string_expanded == "":
              char_string_expanded = self.insert_between_all_characters_par(char_string,self.control_chars["any_characters"])
            d = self.filter_dict(char_string_expanded,self.master_dict[length])
          else:
            d = self.find_included_words(char_string,length)
          #ret = list(d[x][0] for x in d.keys()) 

        elif anagram_string != "":
          if char_string != "":
            d = self.filter_dict(char_string,self.master_dict[length])
          else:
            d = self.master_dict[length]

            #print(d)

#          print(self.num_combinations(anagram_string,length))
          if (self.num_combinations(anagram_string,length) > self.anagram_max_hash):
#            start_time1 = time.perf_counter()
            d = self.get_all_anagrams1(anagram_string,split_char,group_string,d,length)
#            end_time1 = time.perf_counter()
  #          if char_string != "":
  #            d = self.filter_dict(char_string,d)
          else:
#            start_time2 = time.perf_counter()
            if real_length_anagram_string >= length:
              d = self.get_all_anagrams(anagram_string,split_char,group_string,d,length)
            else:
              d = self.get_all_partial_anagrams(anagram_string,split_char,group_string,d)
#            end_time2 = time.perf_counter()
          #d = {}
              #d = self.get_partial_anagrams_from_dict(anagram_string,d)
  #        print ("Times: ",end_time1 - start_time1,end_time2 - start_time2)

          if split_char != "":
            d = self.filter_match_list(d,anagram_match_list)
        elif misprint_number > 0:
          d = self.get_misprints(char_string,misprint_number,self.master_dict[length])
        else:
          d = self.filter_dict(char_string,self.master_dict[length])
        if spaces > 0:
          d = self.filter_spaces(spaces,d)
        if only_uppercase:
          d = self.filter_uppercase(d)
        #clist[0].count(control_chars["space"])
        sorted_dict = dict(sorted(d.items()))
        if anagram_string != "" and self.all_letters(anagram_string) and len(anagram_string) != length:
          if len(anagram_string) > length:
            dlist = [sorted_dict[x] + ["(-" + "".join(sorted(self.letter_difference(x,anagram_string))) + ")"] for x in sorted_dict.keys()]
          elif len(anagram_string) < length:
            dlist = [sorted_dict[x] + ["(+" + "".join(sorted(self.letter_difference(anagram_string,x))) + ")"] for x in sorted_dict.keys()]
        else:
          dlist = [sorted_dict[x] + [""] for x in sorted_dict.keys()]
  #        dlist = list(sorted_dict.values())
        results += dlist
      ret = list(x[0] + x[2] for x in results) 
    return ret

  def validate_and_execute(self,command):
    kwargs,valid,error_message = self.parse_command(command)
    if valid:
      #start_time = time.perf_counter()
      results = self.main_action(**kwargs)
      #end_time = time.perf_counter()
      #print("Time: ",end_time - start_time)
    else:
      results = []
    return results,valid,error_message

if not utils().is_android():
  class command_line_app:
    def no_kivy_command(self):
      s = solver()
      while True:
        command = input("Enter string:")
        results,valid,error_message = s.validate_and_execute(command)
        if valid:
          for x in results:
            print(x)
          print("total:",len(results))
        else:
          print(error_message)

if ((utils().is_android() or debug_android)):
  class ScrollViewAppScreens(App):
    #from jnius import autoclass
    sv = solver()
  #root.manager.transition.direction = 'left'
    Builder.load_string("""
        #l = Label(text=t,size_hint=(1,None),height="12dp",font_name="DroidSansMono")
<HelpLabel>
  font_size: '15dp'
  height: self.texture_size[1]
  size_hint_y: None
  text_size: self.width, None
  text: root.text
  markup: True
<HistoryButton>:
  text: root.name
  #font_size: '20dp'
  size_hint: 1,None
  height: '20dp'
  font_size: '20dp'
  font_name: 'DroidSansMono' if not self.debug_android else "arial"
  halign: 'left'
  text_size: self.size
  on_release: root.callback(self,self.parent)
<CommandButton>:
  #size_hint_x: 0.1
  #size_hint_y: 0.5
  pos_hint: {'left': .5, 'center_y': .5}
  text: root.name
  font_size: '20dp'
  halign: 'center'
  text_size: self.size
  on_release: root.callback(self,self.parent)
<MainScreen>:
  BoxLayout:
    orientation: 'vertical'
    spacing: 10
    BoxLayout:
      spacing: 1
      orientation: 'horizontal'
      #height: '200dp'
      size_hint_y: .4
      #size:1400,1000
      #pos_hint: {'center_x': .5, 'center_y': 1}
      TextInput:
        size_hint_y:1
        id: t1
        multiline: False
        padding_y: 0
        pos_hint: {'center_x':.5, 'center_y':.5}
        #padding_y: [self.height / 4]
        #size: 100,100
        #height: '200dp'
        font_size: '20dp'
        on_text_validate: root.on_enter()
      Button:
        size_hint: .1,1
        pos_hint: {'center_x':.9, 'center_y':.5}
        font_size: '20dp'
        text: 'X'
        on_press: root.text_erase()
      Button:
        size_hint: .2,1
        pos_hint: {'center_x':.9, 'center_y':.5}
        font_size: '20dp'
        text: 'Search'
        on_press: root.button_callback()
    BoxLayout:
      id: line2
      padding:0
      #spacing: 5
      orientation: 'horizontal'
      #size_hint: 1,4
      size_hint_y: .3
      font_size: '300dp'
      #pos_hint: {'center_x': .5, 'center_y': 0}
    BoxLayout:
      id: line3
      padding:0
      #spacing: 5
      orientation: 'horizontal'
      #size_hint: 1,4
      size_hint_y: .3
      #font_size: '20dp'
      #pos_hint: {'center_x': .5, 'center_y': .85}
    ScrollView:
      #size_hint: None,None
      size_hint_y: 10
      size_hint_x: 1
      #size: 1400,2200
      pos_hint: {'center_x': .5, 'center_y': .7}
      do_scroll_x: False
      do_scroll_y: True
      GridLayout:
        id: layout
        cols: 1
        size_hint: 1, None
        height: self.minimum_height
    BoxLayout:
      spacing: 1
      orientation: 'horizontal'
      size_hint_y: .4
      Button:
        size_hint: .4,.5
        #pos_hint: {'center_x':.8, 'center_y':.5}
        font_size: '15dp'
        text: 'Command History'
        on_release: root.manager.current = 'history'
      Button:
        size_hint: .4,.5
        #pos_hint: {'center_x':.8, 'center_y':.5}
        font_size: '15dp'
        text: 'Help'
        on_release: root.manager.current = 'help'
<HistoryScreen>:
  BoxLayout:
    orientation: 'vertical'
    spacing: 5
    ScrollView:
      size_hint: 1,9
      #size: 1400,2600
      #pos_hint: {'center_x': .5, 'center_y': .5}
      do_scroll_x: False
      spacing: 20
      GridLayout:
        id: history
        cols: 1
        size_hint: 1, None
        #pos_hint: {'center_x': .5, 'center_y': 1}
        height: self.minimum_height
    Button:
      size_hint: .2,.3
      pos_hint: {'center_x':.9, 'center_y':2}
      font_size: '15dp'
      text: 'Main Screen'
      on_release: root.manager.current = 'main'
<HelpScreen>:
  BoxLayout:
    orientation: 'vertical'
    spacing: 5
    ScrollView:
      size_hint: 1,9
      #size: 1400,2600
      #pos_hint: {'center_x': .5, 'center_y': .5}
      do_scroll_x: False
      spacing: 20
      GridLayout:
        spacing: 20
        id: help
        cols: 1
        size_hint: 1,None
        height: self.minimum_height
    Button:
      size_hint: .2,.3
      pos_hint: {'center_x':.9, 'center_y':2}
      font_size: '15dp'
      text: 'Main Screen'
      on_release: root.manager.current = 'main'
""")


    class MainScreen(Screen):

      def create_label(self,t):
        #l = Label(text=t,size_hint=(1,None),height="12dp",font_name="DroidSansMono")
        if debug_android:
          l = Label(text=t,size_hint=(1,None),height="12dp")
        else:
          l = Label(text=t,size_hint=(1,None),height="12dp",font_name="DroidSansMono")
        l.bind(size=l.setter('text_size'))
        return l
      

      def execute(self):
        sv = ScrollViewAppScreens.sv
        self.ids.layout.clear_widgets()
        results,valid,error_message =  sv.validate_and_execute(self.ids.t1.text)
        if valid:
          total = len(results)
          for x in results:
            self.ids.layout.add_widget(self.create_label(x))
          self.ids.layout.add_widget(self.create_label("Total: " + str(total)))
        else:
          self.ids.layout.add_widget(self.create_label(error_message))

      def on_enter(self):
        self.execute()
  
      def button_callback(self):
        self.execute()

      def text_erase(self):
        self.ids.t1.text = ""
        Clock.schedule_once(self.text_get_focus,.1)

      def text_get_focus(self,widget):
        self.ids.t1.focus = True

      def text_update(self, *args, **kwargs):
        self.ids.t1.insert_text(args[0])
        Clock.schedule_once(self.text_get_focus,.1)
        
      def test_update(self,*args, **kwargs):
        #self.ids.t1.insert_text("test_update pressed")
        self.ids.t1.text = ""
        self.ids.t1.insert_text("Q")
        #self.ids.t1.text = "test_update!!!"

      def test_update1(self):
        self.ids.t1.insert_text("test_update1 pressed")
      

      def add_command_buttons(self,sm,s):
        sv = ScrollViewAppScreens.sv
        for b in sv.control_chars.keys():
          #but =  Button(size_hint =(.1, .03),pos_hint ={'left':.1, 'center_y':.5},text = "But")
          but =  Button(size_hint =(.1, .5),pos_hint ={'left':.1, 'center_y':.5},text = sv.control_chars[b], on_press=partial(self.text_update,sv.control_chars[b]))
          #but.bind(on_press=partial(self.text_update,sv.control_chars[b]))
          #but.bind(on_press=self.test_update)
          sm.get_screen('main').ids.line2.add_widget(but)
          #sm.get_screen('main').ids.t1.insert_text("Q")




#End of MainScreen


    class CommandButton(Button):
      def __init__(self, ms):
        super().__init__()
        self.ms = ms
      
      name = StringProperty()
      def text_get_focus(self,widget):
        self.ms.ids.t1.focus = True
      
      def callback(self, widget ,*args, **kwargs):
        self.ms.ids.t1.insert_text(self.name)
        Clock.schedule_once(self.text_get_focus,.1)



    def add_command_buttons1(self,sm,s):
      max_buttons = 10
      but_number = 0
      #sv = ScrollViewAppScreens.sv
      for b in self.sv.control_chars.keys():
        but_number += 1
        but =  self.CommandButton(sm.get_screen('main'))
        setattr(but, "name",self.sv.control_chars[b])
        but.bind(size=but.setter('text_size'))

        if but_number <= max_buttons:
          sm.get_screen('main').ids.line2.add_widget(but)
        else:
          sm.get_screen('main').ids.line3.add_widget(but)
        #sm.get_screen('main').ids.t1.insert_text("Q")

#    def add_command_buttons(self,sm,s):
#      ms = self.MainScreen()
#      for b in self.sv.control_chars.keys():
#        #but =  Button(size_hint =(.1, .03),pos_hint ={'left':.1, 'center_y':.5},text = "But")
#        but =  Button(size_hint =(.1, .5),pos_hint ={'left':.1, 'center_y':.5},text = self.sv.control_chars[b])
#        #but.bind(on_press=partial(ms.text_update,self.sv.control_chars[b]))
#        but.bind(on_press=self.ids.t1.insert_text(self.sv.control_chars[b]))
#        sm.get_screen('main').ids.line2.add_widget(but)


    class HistoryScreen(Screen):
#      def __init__(self):
#        super().__init__()

      class HistoryButton(Button):
        def __init__(self,debug_android):
          self.debug_android = debug_android
          super().__init__()

          #self.sm = ScreenManager()
          #self.ms = self.sm.get_screen('main')

        def text_get_focus(self,widget):
          sm = App.get_running_app().root
          ms = sm.get_screen('main')
          ms.ids.t1.focus = True
        
        name = StringProperty()
        def callback(self, widget ,*args, **kwargs):
          sm = App.get_running_app().root
          ms = sm.get_screen('main')
          ms.ids.t1.text = self.name
          sm.current = "main"
          Clock.schedule_once(self.text_get_focus,.1)


      def create_button(self,t):
        #l = Label(text=t,size_hint=(1,None),height="12dp",font_name="DroidSansMono")
        #l = Button(text=t,size_hint=(1,None),height="12dp")
        b = self.HistoryButton(debug_android)
        b.name = t
        b.bind(size=b.setter('text_size'))
        return b

      def on_pre_enter(self, *args):
        self.write_command_history()

      def write_command_history(self):
        sv = ScrollViewAppScreens.sv
        self.ids.history.clear_widgets()
        for c in sorted(set(sv.command_history)):
          self.ids.history.add_widget(self.create_button(c))


    class HelpScreen(Screen):

      class HelpLabel(Label):
        def __init__(self):
          super().__init__()

      class WrappedLabel(Label):
      # Based on Tshirtman's answer
        def __init__(self, **kwargs):
          super().__init__(**kwargs)
          self.bind(
            width=lambda *x:
            self.setter('text_size')(self, (self.width, None)),
            texture_size=lambda *x: self.setter('height')(self, self.texture_size[1]))

      def on_pre_enter(self, *args):
        self.write_help()
      
      def create_label(self,t):
        #l = Label(text=t,size_hint=(1,None),height="12dp",font_name="DroidSansMono")
#        l = Label(text=t,size_hint=(None,None),text_size=(self.width,None),height="12dp")
#        l = Label(text=t,size_hint=(2,None),height="12dp")
#        l.bind(size=l.setter('text_size'))
        #l = self.WrappedLabel(text = t,bold = False,font_size = "15dp",markup = True)
        l = self.HelpLabel()
        setattr(l, "text",t)
        return l
      
      def write_help(self):
        sv = ScrollViewAppScreens.sv
        self.ids.help.clear_widgets()
        for x in sv.master_control.items():
          self.ids.help.add_widget(self.create_label("[b][size=18dp]" + escape_markup(str(x[1][0])) + "[/size][/b] " + escape_markup(str(x[1][1])) + " eg: "  + escape_markup(str(x[1][2]))))


    def build(self):
      sm = ScreenManager()
      #ms = self.MainScreen()
      sm.add_widget(self.MainScreen(name='main'))
      sm.add_widget(self.HistoryScreen(name='history'))
      sm.add_widget(self.HelpScreen(name='help'))
      sm.current = "main"
      self.add_command_buttons1(sm,self.MainScreen())

      return sm


#if __name__ == '__main__':
#  ScrollViewAppScreens().run()


if __name__ == '__main__':
  if ((utils().is_android() or debug_android)):
    ScrollViewAppScreens().run()
  else:
    command_line_app().no_kivy_command()
