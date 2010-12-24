#!/usr/bin/python
# Run magic.toplevel(the MagicInstaller main program), to install your system.

import os
import sys
import isys
from mipublic import *
from cleanenv import *

# Search magic.toplevel file and Run it.
magicToplevelFile = ''
magicToplevelFile = search_file('magic.toplevel', [hotfixdir, '/usr/bin'],
        exit_if_not_found = False) or magicToplevelFile
magicToplevelFile = search_file('magic.toplevel.py', [hotfixdir, '/usr/bin'],
        exit_if_not_found = False) or magicToplevelFile
if magicToplevelFile:
    os.execl('/usr/bin/python', '/usr/bin/python', magicToplevelFile)
else:
    print 'Cannot find setup program.'
