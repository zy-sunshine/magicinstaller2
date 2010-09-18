#!/usr/bin/python
# Run magic.toplevel(the MagicInstaller main program), to install your system.

import os
import sys
import isys
from mipublic import *
#from miutil import *
ALL_FREE_LOOP = ['/dev/loop0', '/dev/loop1', '/dev/loop2', '/dev/loop3',
             '/dev/loop4', '/dev/loop5', '/dev/loop6', '/dev/loop7']

# umount all dir from loop device.
loop_dirs = ['/tmpfs/mnt/loop3']
for loop_dir in loop_dirs:
    if os.path.exists(loop_dir):
        umount_dev(loop_dir)
        remove_empty_dir(loop_dir)

# detach all iso file from loop device
for lo in ALL_FREE_LOOP:
    if os.path.exists(lo):
        ret, msg = isys.loopstatus(lo)
        if ret:
            os.system('losetup -d %s' % lo)

# umount mounted dir.
tmpfs_mnt_dir = '/tmpfs/mnt'
if os.path.exists(tmpfs_mnt_dir):
    for d in os.listdir(tmpfs_mnt_dir):
        umount_dev(os.path.join(tmpfs_mnt_dir, d))
        remove_empty_dir(os.path.join(tmpfs_mnt_dir, d))

# umount target system dir.
if os.path.exists('/tmpfs/tgtsys'):
    umount_dev('/tmpfs/tgtsys')
    remove_empty_dir('/tmpfs/tgtsys')

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
