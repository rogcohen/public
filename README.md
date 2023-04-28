# crossword_helper
This is an attempt to emulate in Python (most) of the functionality of Simon Long's excellent IOS app "Advanced Crossword Solver",
available from KuDaTa Software (https://apps.apple.com/gb/developer/kudata-software). If you have an IOS phone I urge you to get that app.

I started this project because the app wasn't available on Android; when I switched to an Android phone from IOS that was the most
annoying problem. It was also an opportunity to write something more substantial in Python than the small utilities I use to help with 
numerical puzzles.

crossword_helper was developed on a Windows 10 pc and has only been tested on my Samsung Galaxy X21 phone running as a program on the Pydroid app. It uses the Kivy framework to handle the UI, to which I have given only the minimal attention necessary to get it to work at all.

crossword_helper must be supplied with file(s) containing word lists to work. I used lists derived from Ross Beresford's UK Advanced Cryptics Dictionary
(http://cfajohnson.com/wordfinder/UKACD17.shtml) and the enable1.txt word list available from https://code.google.com/archive/p/dotnetperls-controls/downloads (among others). Crossword-helper starts up fastest when the word file(s) are split into mutiple files each containing a single length of word. Each row contains three "|" separaated fields: <Word cast to lowwer case with all accents and spaces etc removed>|<Original word>|<Numerical hash of the first field>. The program split_text_file.py will create the necessary multiple files from a file containing a raw word list. There is also a commented-out section in crossword_helper that will load the lists from any number of single files containing lists of words of any lengths.

I have so far failed to compile this code into a proper Android app - I've only tried the GitHub workflow built-in compiler. The problem seems to lie with the Kivy fromework, since a small test app also failed to compile. The compile completes successfully but the resulting package always crashes on startup.
