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


kernelver      = '2.6.28.10'  # The kernel used by installer.
distname       = 'MagicLinux'
distver        = '2.5'
isofn_fmt      = '%s-%s-%d.iso'
bootcdfn       = 'MagicLinux-2.5-1.iso'
tgtsys_root    = '/tmpfs/tgtsys'
distkernelver  = '2.6.30.10-smp'
kernel_fn      = 'vmlinuz-%s' % distkernelver
initrd_fn      = 'initrd-%s.img' % distkernelver

hotfixdir      = '/tmp/update'

BINDIR         = '/usr/bin'
DATADIR        = '/usr/share/MagicInstaller'
LIBDIR         = '/usr/lib/python2.6/site-packages'
MODULEDIR      = '/usr/share/MagicInstaller/modules'
OPERATIONDIR   = '/usr/share/MagicInstaller/operations'
TEXTDOMAIN     = 'magic.installer'

full_width     = 640
full_height    = 480
help_width     = full_width * 0.6
help_height    = full_height * 0.9

MBRoot         = '/mnt/MagicBooter'

dolog         = True

useudev       = True

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
    'ntfs':       ('ntfs',   '/sbin/mkfs.ntfs -Q',         1,    -1,  ''),
    'reiserfs':   ('reiserfs', '/sbin/mkreiserfs -f -f',   33,   -1, 'b'),
    'xfs':        ('xfs',      '/sbin/mkfs.xfs -q -f',      5,   -1, 'b')
    }

# Get MagicBooter parameter from mbsave.py
EXPERT_MODE = 0
RESCUE_MODE = 0
TEXT_MODE = 0
try:
    if useudev:
        execfile('/etc/mbsave.py')
    else:
        import os
        execfile(os.path.join(MBRoot, 'mbsave.py'))
except Exception, errmsg:
    print str(errmsg)

from miutil import *

