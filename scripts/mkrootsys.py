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
import sys
import stat

cmds = []
todir = sys.argv[1]

useudev = False
for arg in sys.argv:
    if arg == '--use-udev':
        useudev = True

# Create the required directories and some files.
cpcmd = 'cp -a --no-preserve=ownership'
#mountpoints = "mnt,device.mnt,mnt1,mnt2,mnt3"
cmds.append('mkdir -p %s/{dev,etc,proc,sys,mnt}' % todir)
cmds.append('mkdir -p %s/etc/sysconfig' % todir)
cmds.append('mkdir -p %s/tmpfs/var/log' % todir)
#cmds.append('mkdir -p %s/mnt/miroot' % todir)
#cmds.append('mkdir -p %s/tmp/{%s}' % (todir, mountpoints))

# Remove .sconsign
cmds.append('find %s -name .sconsign | xargs rm -f' % todir)

### For MagicBooter, so remove it.
# Link 'linuxrc' to 'bin/magicbooter'.
# Refer the README in magicbooter directory before add/remove of the included applets.
#bin_links = ['cpio', 'gunzip', 'mount', 'sh', 'umount', 'ls', 'cat', 'mv']
#sbin_links = ['ifconfig', 'init', 'insmod', 'modprobe', 'rmmod', 'route', 'mdev']
#usrbin_links = ['wget']
#cmds.append('mkdir -p %s %s %s' % \
#            (os.path.join(todir, 'bin'),
#             os.path.join(todir, 'sbin'),
#             os.path.join(todir, 'usr/bin')))
#for link in bin_links:
#    cmds.append('ln -s ../sbin/magicbooter %s' % \
#                os.path.join(todir, 'bin', link))
#for link in sbin_links:
#    cmds.append('ln -s magicbooter %s' % \
#                os.path.join(todir, 'sbin', link))
#for link in usrbin_links:
#    cmds.append('ln -s ../../sbin/magicbooter %s' % \
#                os.path.join(todir, 'usr/bin', link))
# add a /init link

cmds.append('ln -s bin/busybox %s' % \
            os.path.join(todir, 'init'))

for cmd in cmds:
    print cmd
    if os.system(cmd) != 0:
        sys.exit(1)

def crange(c_from, c_to):
    return  map(lambda i: chr(i), range(ord(c_from), ord(c_to)))

def create_block_dev(dev_name, major, minor):
    os.mknod(os.path.join(todir, 'dev', dev_name),
             0660 | stat.S_IFBLK,
             os.makedev(major, minor))

def create_char_dev(dev_name, major, minor):
    os.mknod(os.path.join(todir, 'dev', dev_name),
             0660 | stat.S_IFCHR,
             os.makedev(major, minor))

if not useudev:
    # cmds.append('%s /dev/ram[01] /dev/loop[4-7] %s/dev' % (cpcmd, todir))
    for i in [0, 1]:
        create_block_dev('ram%d' % i, 1, i)

    for i in xrange(4, 8):
        create_block_dev('loop%d' % i, 7, i)

    #cmds.append('%s /dev/sd[a-h] /dev/sd[a-h][1-9] /dev/sd[a-h]1[0-9] %s/dev' % (cpcmd, todir))
    m = { 'a': (8,  0), 'b': (8, 16), 'c': (8,  32), 'd': (8, 48),
          'e': (8, 64), 'f': (8, 80), 'g': (8,  96), 'h': (8, 112) }
    for hd in crange('a', 'i'):
        major, minor = m[hd]
        create_block_dev('sd%c' % hd, major, minor)
        for part in xrange(1, 16):
            create_block_dev('sd%c%d' % (hd, part), major, minor + part)

    #cmds.append('%s /dev/hd[a-h]* %s/dev' % (cpcmd, todir))
    m = { 'a': (3,   0), 'b': (3,  64), 'c': (22,  0), 'd': (22, 64),
          'e': (33,  0), 'f': (33, 64), 'g': (34,  0), 'h': (34, 64) }
    for hd in crange('a', 'i'):
        major, minor = m[hd]
        create_block_dev('hd%c' % hd, major, minor)
        for part in xrange(1, 33):
            create_block_dev('hd%c%d' % (hd, part), major, minor + part)

# Create the required device files.
# for d in ['console', 'null', 'zero',
#           'tty', 'tty0', 'tty1', 'tty2', 'tty3', 'tty4', 'tty5', 'tty6']:
#     cmds.append('%s /dev/%s %s/dev' % (cpcmd, d, todir))
m = { 'console': ('c', 5, 1),
      'null': ('c', 1, 3),
      'zero': ('c', 1, 5) }
for dev_name in m:
    if m[dev_name][0] == 'b':
        create_block_dev(dev_name, m[dev_name][1], m[dev_name][2])
    else:
        create_char_dev(dev_name, m[dev_name][1], m[dev_name][2])

create_char_dev('tty', 5, 0)
for i in xrange(0, 7):
    create_char_dev('tty%d' % i, 4, i)

