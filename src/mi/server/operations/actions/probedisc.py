import os, time
from mi.server.utils import logger, CF
from mi.server.utils.device import MiDevice
from mi.utils.miregister import MiRegister
register = MiRegister()

####################### ?????????? ###############################
cur_rpm_fd = 0
ts = None

rpmdb = 'rpmdb.tar.bz2'
etctar = 'etc.tar.bz2'
etc_script = 'etc_install.sh'
tmp_config_dir = 'tmp/MI_configure'

dev_hd = None # the harddisk device where save packages.
dev_iso = None # the iso where save pkgs.
dev_tgt = None # the target system device.
#############################################################

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
        logger.e('probe_all_disc iso format is wrong: bootiso_relpath: %s bootiso_fn: %s', (bootiso_relpath, bootiso_relpath))
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
                        os.path.normpath(os.path.join(relative_dir, os.path.basename(pkgpath))) )
        else:
            # deal with harddisk case
            pkgs = [ os.path.join(p, disc_first_pkgs[disc_no]) for p in pkg_probe_path ]
            for f, reldir in midev.iter_searchfiles(pkgs, [pkgarr_reldir]):
                probe_ret = ('', os.path.join(reldir, os.path.basename(f)))
        if probe_ret:
            result.append(probe_ret)

    logger.i('probe_all_disc return result is : %s\n' % str(result))
    return  result
    
class MiDevice_TgtSys(object):
    def __init__(self, tgtsys_devinfo):
        self.mounted_devs = []
        self.tgtsys_devinfo = tgtsys_devinfo
        
    def mount_tgt_device(self):
        tgt_root_dev, tgt_root_type = self.tgtsys_devinfo['/']
        tgt_boot_dev, tgt_boot_type = self.tgtsys_devinfo['/boot']
        tgt_swap_dev = self.tgtsys_devinfo['swap'][0]
        if tgt_swap_dev:
            #### swap on or not
            pass
        #### mount root device
        mnt_point = CF.D.TGTSYS_ROOT
        dev_tgt_root = MiDevice(tgt_root_dev, tgt_root_type, mnt_point)
        if not dev_tgt_root.do_mount(): #### NOTE: carefully handle this device's mount.
            logger.e('Mount device %s Failed, install operate can not continue' % dev_tgt_root.get_dev())
            return False
        else:
            self.mounted_devs.append(dev_tgt_root)
        
        if tgt_boot_dev and (tgt_boot_dev != tgt_root_dev):
            #### mount boot device
            mnt_point = os.path.join(CF.D.TGTSYS_ROOT, 'boot')
            dev_tgt_boot = MiDevice(tgt_boot_dev, tgt_boot_type, mnt_point)
            if not dev_tgt_boot.do_mount(): #### NOTE: carefully handle this device's mount.
                logger.e('Mount device %s Failed, install operate can not continue' % dev_tgt_boot.get_dev())
                self.umount_tgt_device()
                return False
            else:
                self.mounted_devs.append(dev_tgt_boot)
        return True
                
    def umount_tgt_device(self):
        self.mounted_devs.reverse()
        for dev in self.mounted_devs:
            if not dev.do_umount():
                logger.w('Umount device %s Failed, but we continue')

@register.server_handler('long')
def instpkg_prep(mia, operid, pkgsrc_devinfo, tgtsys_devinfo):
    '''
        Install all package prepare work.
        We should mount target system device, to prepare install packages.
        and mount disk which packages source is saved on.
    '''

    global dev_hd # the harddisk device where save packages.
    global dev_iso # the iso where save pkgs.
    global dev_tgt # the target system devices.
    
    dev, fstype, bootiso_relpath, reldir = pkgsrc_devinfo

    logger.i('instpkg_prep(%s, %s, %s, %s)\n' % (dev, fstype, bootiso_relpath, reldir))
    
    ############################## Mount Start #####################################            
    dev_tgt = MiDevice_TgtSys(tgtsys_devinfo)
    if not dev_tgt.mount_tgt_device(): #### NOTE: carefully handle this device's mount.
        msg = 'Mount target system devices Failed, install operate can not continue!!!'
        logger.e(msg)
        dev_tgt = None
        return msg
    ############################## Mount Finished #####################################
    #--- This code is according to rpm.spec in rpm-4.2-0.69.src.rpm. ---
    # This code is specific to rpm.
    import pdb; pdb.set_trace()
    var_lib_rpm = os.path.join(CF.D.TGTSYS_ROOT, 'var/lib/rpm')
    if not os.path.isdir(var_lib_rpm):
        os.makedirs(var_lib_rpm)
        
    return  0


@register.server_handler('long')
def instpkg_disc_prep(mia, operid, dev, reldir, fstype, bootiso_relpath):
    '''
        Install each disc prepare work.
        We should mount each iso to prepare packages source(for disc).
    '''
    global dev_hd # the harddisk device where save packages.
    global dev_iso # the iso where save pkgs.
    logger.i('instpkg_disc_prep(%s, %s, %s, %s)\n' % \
          (dev, reldir, fstype, bootiso_relpath))
    ############################## Mount Start #####################################
    dev_hd = MiDevice(dev, fstype)
    if not dev_hd.do_mount(): #### NOTE: carefully handle this device's mount.
        msg = 'Mount device %s Failed, install operate can not continue' % dev_hd.get_dev()
        logger.e(msg)
        return msg
        
    if bootiso_relpath:
        # an iso file on harddisk
        dev_iso = MiDevice(dev_hd.get_file_path(bootiso_relpath), 'iso9660')
        if not dev_iso.do_mount(): #### NOTE: carefully handle this device's mount.
            dev_hd.do_umount(); dev_hd = None
            msg = 'Mount device %s Failed, install operate can not continue!!!' % dev_iso.get_dev()
            logger.e(msg)
            dev_iso = None
            return msg
            
    ############################## Mount Finished #####################################
    return  0

@register.server_handler('long')
def instpkg_disc_post(mia, operid, dev, fstype, reldir, bootiso_relpath, first_pkg):
    global dev_hd # the harddisk device where save packages.
    global dev_iso # the iso where save pkgs.
    logger.i('instpkg_disc_post(%s, %s, %s, %s, %s)\n' % \
          (dev, fstype, reldir, bootiso_relpath, first_pkg))
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
