#!/usr/bin/python
import os, glob, sys
import isys
from mi.utils import _
from mi import getdev
from mi.utils.common import mount_dev, umount_dev
from mi.utils.miconfig import MiConfig
from mi.server.utils.device import MiDevice
CF = MiConfig.get_instance()

from mi.utils.miregister import MiRegister
register = MiRegister()

from mi.server.utils import logger
dolog = logger.info

dev_hd = None # the harddisk device where save packages.
dev_iso = None # the iso where save pkgs.
dev_tgt = None # the target system devices.
inst_h = None   # install package handler
dev_mnt_dir = '/' # the current hd or iso mount dir

class MiDevice_TgtSys(object):
    def __init__(self, tgtsys_devinfo):
        self.mounted_devs = []
        # [['/', '/dev/sdb2', 'ext4'], ['USE', '/dev/sdb1', 'linux-swap']]
        self.tgtsys_devinfo = tgtsys_devinfo
        
    def get_devinfo_by_mpoint(self, mpoint):
        for devinfo in self.tgtsys_devinfo:
            if devinfo[0] == mpoint:
                return devinfo[1], devinfo[2]
        return None, None
    
    def mount_tgt_device(self):
        tgt_root_dev, tgt_root_type = self.get_devinfo_by_mpoint('/')
        
        tgt_swap_dev, tgt_swap_type = self.get_devinfo_by_mpoint('USE')
        if tgt_swap_dev and os.path.exists(tgt_swap_dev):
            os.system('swapon %s' % tgt_swap_dev)

        #### mount root device
        mnt_point = CF.D.TGTSYS_ROOT
        dev_tgt_root = MiDevice(tgt_root_dev, tgt_root_type, mnt_point)
        if not dev_tgt_root.do_mount(): #### NOTE: carefully handle this device's mount.
            logger.e('Mount device %s Failed, install operate can not continue' % dev_tgt_root.get_dev())
            return False
        else:
            self.mounted_devs.append(dev_tgt_root)
        def mount_each(tgt_root_dev, tgt_other_dev, tgt_other_type, tgt_other_mpoint):
            if tgt_other_dev and tgt_root_dev != tgt_other_dev:
                mnt_point = os.path.join(CF.D.TGTSYS_ROOT, tgt_other_mpoint.lstrip('/'))
                dev_tgt_other = MiDevice(tgt_other_dev, tgt_other_type, mnt_point)
                
                if not dev_tgt_other.do_mount(): #### NOTE: carefully handle this device's mount.
                    logger.e('Mount device %s Failed, install operate can not continue' % dev_tgt_other.get_dev())
                    self.umount_tgt_device()
                    return False
                else:
                    self.mounted_devs.append(dev_tgt_other)
                    
        for mpoint, dev_, type_ in self.tgtsys_devinfo:
            if mpoint not in ('/', 'USE'):
                mount_each(tgt_root_dev, dev_, type_, mpoint)
        
        # mount -t proc proc myroot/proc/
        mnt_point = os.path.join(CF.D.TGTSYS_ROOT, 'proc')
        mount_dev('proc', 'proc', mntdir=mnt_point,flags=None)
        self.mounted_devs.append(mnt_point)
        # mount -t sysfs sys myroot/sys/
        mnt_point = os.path.join(CF.D.TGTSYS_ROOT, 'sys')
        mount_dev('sysfs', 'sys', mntdir=mnt_point,flags=None)
        self.mounted_devs.append(mnt_point)
        # mount -o bind /dev myroot/dev/
        mnt_point = os.path.join(CF.D.TGTSYS_ROOT, 'dev')
        mount_dev(None, '/dev', mntdir=mnt_point,flags='bind')
        self.mounted_devs.append(mnt_point)
        
        return True
                
    def umount_tgt_device(self):
        self.mounted_devs.reverse()
        for dev in self.mounted_devs:
            if type(dev) is MiDevice:
                if not dev.do_umount():
                    logger.w('Umount device %s Failed, but we continue')
            else:
                umount_dev(dev)
                
@register.server_handler('long')
def mount_tgtsys(mia, operid, tgtsys_devinfo):
    dolog('mount_tgtsys %s' % repr(tgtsys_devinfo))
    global dev_tgt # the target system devices.
    logger.d('######### Mount target system (please check the umount point) #############')            
    dev_tgt = MiDevice_TgtSys(tgtsys_devinfo)
    if not dev_tgt.mount_tgt_device(): #### NOTE: carefully handle this device's mount.
        msg = _('Mount target system devices Failed, install operate can not continue!!!')
        logger.e(msg)
        dev_tgt = None
        return msg
    return 0
    
@register.server_handler('long')
def install_prep(mia, operid, pkgsrc_devinfo, tgtsys_devinfo):
    '''
        Install all package prepare work.
        We should mount target system device, to prepare install packages.
        and mount disk which packages source is saved on.
    '''    
    dev, fstype, bootiso_relpath, reldir = pkgsrc_devinfo

    dolog('install_prep(%s, %s, %s, %s)\n' % (dev, fstype, bootiso_relpath, reldir))
    return mount_tgtsys(mia, operid, tgtsys_devinfo)

@register.server_handler('long')
def umount_tgtsys(mia, operid, tgtsys_devinfo):
    dolog('umount_tgtsys %s' % repr(tgtsys_devinfo))
    logger.d('######### UMount target system (please check the mount point) #############') 
    global dev_tgt # the target system devices.
    logger.d('umount dev_tgt %s' % dev_tgt)
    if dev_tgt:
        dev_tgt.umount_tgt_device()
        dev_tgt = None
    return 0

@register.server_handler('long')
def install_post(mia, operid, pkgsrc_devinfo, tgtsys_devinfo):
    dev, fstype, bootiso_relpath, reldir = pkgsrc_devinfo
    dolog('install_post(%s, %s, %s, %s)\n' % (dev, fstype, bootiso_relpath, reldir))
    return umount_tgtsys(mia, operid, tgtsys_devinfo)
    
@register.server_handler('long')
def install_disc_prep(mia, operid, dev, fstype, bootiso_relpath, reldir):
    '''
        Install each disc prepare work.
        We should mount each iso to prepare packages source(for disc).
    '''
    global dev_hd # the harddisk device where save packages.
    global dev_iso # the iso where save pkgs.
    global dev_mnt_dir # the current hd or iso mount dir
    dolog('instpkg_disc_prep(%s, %s, %s, %s)\n' % \
          (dev, fstype, bootiso_relpath, reldir))
    ############################## Mount Start #####################################
    dev_hd = MiDevice(dev, fstype)
    if not dev_hd.do_mount(): #### NOTE: carefully handle this device's mount.
        msg = 'Mount device %s Failed, install operate can not continue' % dev_hd.get_dev()
        logger.e(msg)
        return msg
    dev_mnt_dir = dev_hd.get_mountdir()    
    if bootiso_relpath:
        # an iso file on harddisk
        dev_iso = MiDevice(dev_hd.get_file_path(bootiso_relpath), 'iso9660')
        if not dev_iso.do_mount(): #### NOTE: carefully handle this device's mount.
            dev_hd.do_umount(); dev_hd = None
            msg = 'Mount device %s Failed, install operate can not continue!!!' % dev_iso.get_dev()
            logger.e(msg)
            dev_iso = None
            return msg
        dev_mnt_dir = dev_iso.get_mountdir()
    
    ############################## Mount Finished #####################################
    return  0

@register.server_handler('long')
def install_disc_post(mia, operid, dev, fstype, bootiso_relpath, reldir):
    global dev_hd # the harddisk device where save packages.
    global dev_iso # the iso where save pkgs.
    dolog('instpkg_disc_post(%s, %s, %s, %s)\n' % \
          (dev, fstype, reldir, bootiso_relpath))

    ################################ Umount Start #####################################
    if dev != dev_hd.get_dev():
        msg = 'Error: previous use device %s, this time umount device %s, both should be equal, the install operate can not continue!!!' % (dev_hd.get_dev(), dev)
        logger.e(msg)
        return msg
    if dev_iso:
        if not dev_iso.do_umount():
            msg = 'Umount previous iso %s Failed, install operate can not continue!!!' % dev_iso.get_dev()
            logger.e(msg)
            return msg
        dev_iso = None
    if dev_hd:
        if not dev_hd.do_umount():
            msg = 'Umount previous iso %s Failed, install operate can not continue!!!' % dev_hd.get_dev()
            logger.e(msg)
            return msg
        if dev_hd.get_fstype() == 'iso9660':
            # Eject the cdrom after used.
            try:
                cdfd = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
                isys.ejectcdrom(cdfd) # TODO: ejectcdrom use other method
                os.close(cdfd)
            except Exception, errmsg:
                logger.e('Eject(%s) failed: %s' % \
                            (dev, str(errmsg)))
                return str(errmsg)
        dev_hd = None
    
    ################################ Umount Finished #####################################
    return  0

@register.server_handler('long')
def probe_all_disc(mia, operid, device, devfstype, bootiso_relpath, pkgarr_reldir, disc_first_pkgs):
    '''
        probe the package from all disk
        bootiso_relpath is the first iso path relative path of device /
        pkgarr_reldir is the relative directory path of pkgarr.py of device / OR iso dir /
    '''
    logger.i('probe_all_disc(%s, %s, %s, %s, %s)\n' % \
          (device, devfstype, bootiso_relpath, pkgarr_reldir, disc_first_pkgs))
    
    midev = MiDevice(device, devfstype)
    bootiso_fn = CF.D.ISOFN_FMT % (CF.D.DISTNAME, CF.D.DISTVER, 1)
    # If probe in iso ,but bootiso_fn is not match error occur
    if bootiso_relpath and not os.path.basename(bootiso_relpath) == bootiso_fn:
        logger.e('probe_all_disc iso format is wrong: bootiso_relpath: %s bootiso_fn: %s' % (bootiso_relpath, bootiso_fn))
        return None
    probe_ret = None
    result = []
    for disc_no in range(len(disc_first_pkgs)):
        pkg_probe_path = [  '../packages',
                            'packages',
                            '../packages-%d' % (disc_no + 1),
                            'packages-%d' % (disc_no + 1)]
        if bootiso_relpath:
            # deal with iso case
            iso_fn = CF.D.ISOFN_FMT % (CF.D.DISTNAME, CF.D.DISTVER, disc_no + 1)
            iso_relpath = os.path.join(os.path.dirname(bootiso_relpath), iso_fn)
            pkgarr_reldirs = [ os.path.join(pkgarr_reldir, p) for p in pkg_probe_path ]
            for f, reldir in midev.iter_searchfiles([iso_relpath], ['']): # from disk
                midev_iso = MiDevice(f, 'iso9660')
                for pkgpath, relative_dir in midev_iso.iter_searchfiles([disc_first_pkgs[disc_no]], pkgarr_reldirs): # from iso
                    probe_ret = ( os.path.join(os.path.dirname(bootiso_relpath), iso_fn), 
                        os.path.normpath(os.path.join(relative_dir, pkgpath)) )
        else:
            # deal with harddisk case
            pkgs = [ os.path.join(p, disc_first_pkgs[disc_no]) for p in pkg_probe_path ]
            for f, reldir in midev.iter_searchfiles(pkgs, [pkgarr_reldir]):
                probe_ret = ('', os.path.normpath(os.path.join(reldir, f)))
        if probe_ret:
            result.append(probe_ret)

    dolog('probe_all_disc return result is : %s\n' % str(result))
    return  result


class Progress_CB(object):
    def __init__(self, mia, operid):
        self.mia = mia
        self.operid = operid
        
    def set_step(self, step, total):
        self.mia.set_step(self.operid, step, total)
         
@register.server_handler('long')
def rpm_pre_install(mia, operid, data):
    '''
    Set global object inst_h, used by install package action.
    '''            
    global inst_h
    from mi.server.utils.rpm.pyrpm_install import InstallRpm

    inst_h = InstallRpm(CF.D.TGTSYS_ROOT)
    return inst_h.install_pre()
    
@register.server_handler('long')
def rpm_post_install(mia, operid, data):
    global inst_h
    return inst_h.install_post()
    
@register.server_handler('long')
def rpm_install_pkg(mia, operid, pkg, first_pkg, noscripts):
    global inst_h
    dir_ = os.path.dirname(os.path.join(dev_mnt_dir, first_pkg))
    progress_cb = Progress_CB(mia, operid)
    return inst_h.install('%s/%s' % (dir_, pkg), progress_cb, noscripts)
    
### Test Case
class MiaTest(object):
    def __init__(self):
        from mi.server.utils import FakeMiactions
        self.mia = FakeMiactions()
        self.operid = 999
        
class Test(MiaTest):
    def __init__(self):
        MiaTest.__init__(self)
        
    def test_probe_all_disc(self):
        return probe_all_disc(self.mia, self.operid, '/dev/sda2', 'ext4', 'MagicLinux-2.5-1.iso', 'MagicLinux/base', ['ncurses-base-5.7-2.20090207mgc25.i686.rpm'])
        
if __name__ == '__main__':
    test = Test()
    print test.test_probe_all_disc()

    
