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
changequote(/--, --/)/--
import os,sys
kernelver      = '--/kernelver/--'  # The kernel used by installer.
distname       = '--/distname/--'
distver        = '--/distver/--'
isofn_fmt      = '--/isofn_fmt/--'
bootcdfn       = '--/bootcdfn/--'
tgtsys_root    = '/tmpfs/tgtsys'
distkernelver  = '--/distkernelver/--'
kernel_fn      = 'vmlinuz-%s' % distkernelver
initrd_fn      = 'initrd-%s.img' % distkernelver

hotfixdir      = '--/hotfixdir/--'

BINDIR         = '--/BINDIR/--'
DATADIR        = '--/DATADIR/--'
CURDIR         = os.path.abspath(os.path.curdir)
if not os.path.exists(DATADIR):
    DATADIR = CURDIR
    sys.path.insert(0, os.path.join(CURDIR, 'libs'))
LIBDIR         = '--/LIBDIR/--'
MODULEDIR      = '--/MODULEDIR/--'
OPERATIONDIR   = '--/OPERATIONDIR/--'
TEXTDOMAIN     = '--/TEXTDOMAIN/--'

PKGTYPE        = '--/PKGTYPE/--'

full_width     = --/FULL_WIDTH/--
full_height    = --/FULL_HEIGHT/--
HELP_WIDTH     = int(full_width * 0.6)
HELP_HEIGHT    = int(full_height * 0.9)

MBRoot         = '/mnt/MagicBooter'

dolog         = --/dolog/--

useudev       = --/useudev/--

fstype_map = {
    # fstype : (mount_type, make_command, minsize(m), maxsize(m), flags)
    # For flags:  b: grub can be installed on the partition which contain
    #                this type of filesystem.
    'ext3':       ('ext3',     '/sbin/mkfs.ext3 -I 128',           1,   -1, 'b'),
    'ext2':       ('ext2',     'internal',                  1,   -1, 'b'),
    'ext4':       ('ext4',     '/sbin/mkfs.ext4',           1,   -1, 'b'),
    'fat32':      ('vfat',     'internal',                  1,   -1, 'b'),
    'fat16':      ('vfat',     'internal',                  1, 2048, 'b'),
    'iso9660':    ('iso9660',  '',                         -1,   -1, ''),
    'jfs':        ('jfs',      '/sbin/mkfs.jfs -q',        16,   -1, 'b'),
    'linux-swap': ('',         'internal',                 -1,   -1, ''),
    #'ntfs':       ('ntfs',      '',                          -1,    -1,  ''),
    'ntfs':       ('ntfs-3g',   '/sbin/mkfs.ntfs -Q',         1,    -1,  ''),
    'reiserfs':   ('reiserfs', '/sbin/mkreiserfs -f -f',   33,   -1, 'b'),
    'xfs':        ('xfs',      '/sbin/mkfs.xfs -q -f',      5,   -1, 'b')
    }

# Get MagicBooter parameter from mbsave.py
EXPERT_MODE = 0
RESCUE_MODE = 0
TEXT_MODE = 0
#try:
#    if useudev:
#        execfile('/etc/mbsave.py')
#    else:
#        import os
#        execfile(os.path.join(MBRoot, 'mbsave.py'))
#except Exception, errmsg:
#    print str(errmsg)

from miutil import *
--/
