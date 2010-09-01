#!/usr/bin/python

import string
import sys

import lowlevel

# Usage: python t-lowlevel.py hda:3:0

for dev in sys.argv[1:]:
    (devfn, devmajor, devminor) = string.split(dev, ':')
    print lowlevel.makedev(int(devmajor), int(devminor))
    lowlevel.mknod(devfn, 0600 | lowlevel.S_IFBLK,
                   lowlevel.makedev(int(devmajor), int(devminor)))
