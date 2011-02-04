#!/usr/bin/python

totalsz = 0
path    = 1
group   = 2
deps    = 3
pathes  = 4

arch_map = { 'i386':   ['i386'],
             'i486':   ['i486', 'i386'],
             'i586':   ['i586', 'i486', 'i386'],
             'i686':   ['i686', 'i586', 'i486', 'i386'],
             'athlon': ['athlon', 'i686', 'i586', 'i486', 'i386'],
             'x86_64':   ['x86_64', 'i686', 'i586', 'i486', 'i386'], }
