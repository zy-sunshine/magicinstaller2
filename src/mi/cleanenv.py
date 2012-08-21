#!/usr/bin/python
# clean the environment of last operation, prepare a clean env to install new system.

import os
import sys
#from mipublic import *
from mi.utils.common import mount_dev, umount_dev, remove_empty_dir
import isys
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
tgtsys_dir = '/tmpfs/tgtsys'
if os.path.exists(tgtsys_dir):
    if os.path.exists( os.path.join(tgtsys_dir, 'proc', 'cmdline') ):
        umount_dev(os.path.join(tgtsys_dir, 'proc'))
    if os.path.exists( os.path.join(tgtsys_dir, 'sys', 'block') ):
        umount_dev(os.path.join(tgtsys_dir, 'sys'))
    umount_dev(tgtsys_dir)
    remove_empty_dir(tgtsys_dir)

