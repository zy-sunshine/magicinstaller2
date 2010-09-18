import isys
import sys
import os
sys.path.insert(0, '../../../magic.installer/')
from mipublic import *

if __name__ == '__main__':
    # mount readonly
    # ext_flags = 'ro' , but it need an empty mount device, or it will casue
    # device busy.
    # mount loop device.
    # ext_flags = 'loop' , It can mount a iso and other loop device.

    # isys.mount(fstype, dev_path, mntpoint, ext_flags)
    # isys.umount(mntpoint)
    # isys.swapon(dev_path)
    # isys.swapoff(dev_path)
    # isys.ejectcdrom(dev_fd)
    # isys.sync()

    case = sys.argv[1]
    print case
    my_fs = {"sda9": "ext4",
             "sda12": "ntfs",
             "sda10": "ext2",
             "sda11": "reiserfs",
             "sda8": "ext3",
    }
    if case == '1':
        # Test mount function.
        for key in my_fs.keys():
            fstype = fstype_map[my_fs[key]][0]
            #print fs
            mntpoint = "/media/%s" % key
            dev_path = "/dev/%s" % key
            #ret, msg = mount_dev(fstype, dev_path, mntpoint)
            ret, msg = mount_dev(fstype, dev_path)
            if not ret:
                print msg
    if case == '2':
        # Test iso9660 mount.
        fstype = fstype_map["iso9660"][0]
        dev_path = "/mnt/sda12/MagicLinux-2.5-1.iso"
        mntpoint = "/media/loop1"
        ext_flags = "loop"
        # ext_flags can be remount,ro,user,noauto,unhide... and other optlist in -o
        # option.
        ret, msg = mount_dev(fstype, dev_path, mntpoint, ext_flags)
        if not ret:
            print msg

    if case == '3':
        # Test umount function.
        for key in my_fs.keys():
            mntpoint = "/tmpfs/mnt/%s" % key
            umount_dev(mntpoint)

    if case == '2':
        # Test umount iso function.
        dev_path = "/mnt/sda12/MagicLinux-2.5-1.iso"
        mntpoint = "/media/loop1"
        ret, msg = umount_dev(mntpoint)

    if case == '5':
        # Test ejectcdrom function.
        print "eject cdrom"
        iso_dev = "/dev/loop1"
        f_cd = os.open(iso_dev, os.O_RDONLY | os.O_NONBLOCK)
        try:
            isys.ejectcdrom(f_cd)
        except SystemError, e:
            # like (22, 'Invalid argument')
            #      (5, 'Input/output error')
            # and so on
            print e
        if f_cd:
            os.close(f_cd)

    if case == '6':
        isys.sync()
    if case == '7':
        my_swap = "/dev/sda7"
        isys.swapon(my_swap)
    if case == '8':
        my_swap = "/dev/sda7"
        isys.swapoff(my_swap)
    procpath = 'tgtsys/proc'    
    syspath = 'tgtsys/sys'
    if case == '9':
        if not os.path.exists(procpath):
            os.makedirs(procpath)
        if not os.path.exists(syspath):
            os.makedirs(syspath)
        isys.mount('proc', 'proc', procpath)
        isys.mount('sysfs', 'sys', syspath)
    if case == '10':
        isys.umount(procpath)
        isys.umount(syspath)
        try:
            os.rmdir(procpath)
        except:
            pass
        try:
            os.rmdir(syspath)
        except:
            pass

    #fstype_map[]
