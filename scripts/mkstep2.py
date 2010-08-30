#!/usr/bin/python
# Copyright (C) 2003, Charles Wang.
# Author:  Charles Wang <charles@linux.net.cn>
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANT; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public LIcense for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.

import os
import string
import sys

todir = os.path.abspath(os.getcwd() + '/tmp/mi.rootfs')
bindir = os.path.abspath(os.getcwd() + '/bindir')
fromdir =os.path.abspath(os.getcwd() + '/tmp/root.step0')

useudev = False
for arg in sys.argv:
    if arg == '--use-udev':
        useudev = True

# I must check whether there is any filesystem is mounted on any subdirectory
# in todir. It is realy critical to do this because 'rm -rf todir' might remove
# my system if it is mounted!

f = file('/proc/mounts')
l = f.readline()
ltodir = len(todir)
dangeous_mount = None
while l:
    pieces = string.split(l, ' ')
    if pieces[1][:ltodir] == todir:
        os.write(2, 'DANGEOUS MOUNT: [%s]\n' % str(pieces[:2]))
        dangeous_mount = 'true'
    l = f.readline()
if dangeous_mount:
    os.write(2, 'Please umount the previous mounts firstly!\n')
    sys.exit(-1)

cmds = ['rm -rf %s' % todir,
        'mkdir %s' % todir]
for f in sys.argv:
    if f[:2] == '--':
        continue
    if f[-3:] == '.gz':
        cmds.append('zcat %s | tar x -C %s' % (f, todir))
    elif f[-4:] == '.bz2':
        cmds.append('bzcat %s | tar x -C %s' % (f, todir))

for cmd in cmds:
    print cmd
    if os.system(cmd) != 0:
        sys.exit(1)

# Remove all .sconsign.
cmd = 'find %s -name .sconsign | xargs rm -f' % todir
os.system(cmd)

