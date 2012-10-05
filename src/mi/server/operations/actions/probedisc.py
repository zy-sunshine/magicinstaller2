import os, time, isys
from mi.server.utils import _, logger, CF
from mi.server.utils.device import MiDevice
from mi.utils.miregister import MiRegister
from mi.utils.common import mount_dev, umount_dev
from mi import getdev
import string
register = MiRegister()

####################### ?????????? ###############################
#cur_rpm_fd = 0
#ts = None
#
#rpmdb = 'rpmdb.tar.bz2'
#etctar = 'etc.tar.bz2'
#etc_script = 'etc_install.sh'
#tmp_config_dir = 'tmp/MI_configure'

dev_hd = None # the harddisk device where save packages.
dev_iso = None # the iso where save pkgs.
dev_tgt = None # the target system device.
#############################################################

@register.server_handler('long')
def probe_all_disc(mia, operid, device, devfstype, bootiso_relpath, pkgarr_reldir, disc_first_pkgs):
    '''
        probe the package from all disk
        if there is a cdrom, we can find the first package on it. because we have all first packages list.
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

def _gen_fstab(mount_all_list):
    # Generate fstab.
    mountmap = {}
    for (mntdir, devfn, fstype) in mount_all_list:
        if fstype in ('linux-swap', 'linux-swap(v1)'):
            continue
        if fstype in ('fat32', 'fat16'):
            mountmap[mntdir] = (devfn, CF.D.FSTYPE_MAP[fstype][0],
                                'iocharset=cp936,umask=0,defaults', 0, 0)
        elif mntdir == '/':
            mountmap[mntdir] = (devfn, CF.D.FSTYPE_MAP[fstype][0],
                                'defaults', 1, 1)
        else:
            mountmap[mntdir] = (devfn, CF.D.FSTYPE_MAP[fstype][0],
                                'defaults', 0, 0)
    mountmap['/dev/pts'] = ('none', 'devpts', 'gid=5,mode=620', 0, 0)
    mountmap['/proc']    = ('none', 'proc', 'defaults', 0, 0)
    mountmap['/sys']     = ('none', 'sysfs', 'defaults', 0, 0)
    mountmap['/dev/shm'] = ('none', 'tmpfs', 'defaults', 0, 0)

    
    fdlist = getdev.get_dev_info(getdev.CLASS_FLOPPY)
    for fd_info in fdlist.values():
        mntdir = string.replace(os.path.basename(fd_info.devpath), 'fd', '/media/floppy')
        if mntdir == '/media/floppy0':  mntdir = '/media/floppy'
        mountmap[mntdir] = (fd_info.devpath,
                            'auto', 'iocharset=cp936,noauto,user,rw,exec,sync', 0, 0)
        os.system('mkdir -p %s' % os.path.join(CF.D.TGTSYS_ROOT, mntdir[1:]))

    cdlist = getdev.get_dev_info(getdev.CLASS_CDROM)        
    if cdlist != []:
        cddevlist = [ devinfo['devpath'] for devinfo in cdlist.values() ]
        cddevlist.sort()
        for cnt in range(len(cddevlist)):
            if cnt == 0:
                mntdir = '/media/cdrom'
            else:
                mntdir = '/media/cdrom%d' % cnt
            mountmap[mntdir] = (cddevlist[cnt],
                                'iso9660,udf', 'iocharset=cp936,noauto,user,ro,exec', 0, 0)
            devdir = os.path.join(CF.D.TGTSYS_ROOT, 'dev')
            os.system('mkdir -p %s' % devdir)
            os.system('ln -s %s %s' % \
                      (cddevlist[cnt],
                       os.path.join(devdir,
                                    os.path.basename(mntdir))))
            os.system('mkdir -p %s' % os.path.join(CF.D.TGTSYS_ROOT, mntdir[1:]))
            cnt = cnt + 1
            
    etcpath = os.path.join(CF.D.TGTSYS_ROOT, 'etc')
    if not os.path.isdir(etcpath):
        os.makedirs(etcpath)
    try:
        fstab = file(os.path.join(etcpath, 'fstab'), 'w')
        fstab.write('#%-14s\t%-23s\t%-15s\t%-15s\t%s %s\n' % \
                    ('device', 'mountpoint', 'filesystem', 'options', \
                         'dump', 'checkpassno'))
        mdkeys = mountmap.keys()
        mdkeys.sort()
        for mntdir in mdkeys:
            (dev, fstype, opts, v1, v2) = mountmap[mntdir]
            fstab.write('%-15s\t%-23s\t%-15s\t%-15s\t%d    %d\n' % \
                        (dev, mntdir, fstype, opts, v1, v2))
        for (mntdir, devfn, fstype) in mount_all_list:
            if fstype in ('linux-swap', 'linux-swap(v1)'):
                fstab.write('%-15s\t%-23s\t%-15s\t%-15s\t%d    %d\n' % \
                            (devfn, 'swap', 'swap', 'defaults', 0, 0))
        fstab.close()
    except Exception, errmsg:
        logger.e('Generate fstab failed: %s\n' % str(errmsg))
    return 0

class MiDevice_TgtSys(object):
    def __init__(self, mount_all_list, progress_cb = None):
        self.mounted_devs = []
        self.mount_all_list = mount_all_list
        self.progress_cb = progress_cb
        
    def wait_deivce(self, devfn):
        # Wait for device block appear.
        fblk = False
        trycnt = 0
        for t in range(5):
            if os.system('ls %s' % devfn) == 0:
                fblk = True
                break
            else:
                trycnt += 1
                time.sleep(1)
            
        if not fblk:
            return _('Not exists device block on %s: \ntry time: %d\n') % (devfn, trycnt)
        else:
            return 0
    
    def mount_tgt_device(self):
        errmsg = ''
        if os.path.exists('/tmpfs/debug/nomnttgt'):
            logger.d('TURN ON: nomnttgt\n')
        else:
            # Mount all target partition as the user will.
            cnt = 0
            #mia.set_step(operid, cnt, len(mount_all_list))
            if self.progress_cb:
                self.progress_cb.set_step(cnt, len(self.mount_all_list))
            for (mntpoint, devpath, fstype) in self.mount_all_list:
                if fstype in ('linux-swap', 'linux-swap(v1)'):
                    try:
                        isys.swapon(devpath)
                    except SystemError, em:
                        errmsg += _('swapon(%s) failed: %s') % (devpath, str(em)) 
                        # If reach there, we donnot return, continue remaining operations, to avoid cannot generate fstab case.
                        #return  errmsg
                else:
                    ret = self.wait_deivce(devpath)
                    if ret:
                        if mntpoint == '/':
                            # can find device of mountpoint '/', so we can not continue to install
                            errmsg += _('Can not find device(%s) fstype(%s) of mountpoint("/"), installation can not continue') % (devpath, fstype)
                            logger.e(errmsg)
                            return False, errmsg
                        else:
                            msg = _('Can not find device(%s) fstype(%s) mountpoint("%s") but continue') % (devpath, fstype, mntpoint)
                            logger.w(msg)
                            errmsg += msg
                            continue
                    mount_path = os.path.join(CF.D.TGTSYS_ROOT, mntpoint[1:])
                    dev_obj = MiDevice(devpath, fstype, mount_path)
                    if not dev_obj.do_mount(): #### NOTE: carefully handle these device's mount and umount.
                        if mntpoint == '/':
                            errmsg += _('Mount device(%s) fstype(%s) mountpoint("%s") failed, installation can not continue') % (devpath, fstype, mntpoint)
                            logger.e(errmsg)
                            self.umount_tgt_device()
                            return False, errmsg
                        else:
                            msg = _('Mount device(%s) fstype(%s) mountpoint("%s") failed, but continue') % (devpath, fstype, mntpoint)
                            logger.w(msg)
                            errmsg += errmsg
                    else:
                        self.mounted_devs.append(dev_obj)
                cnt = cnt + 1
                if self.progress_cb:
                    self.progress_cb.set_step(cnt, len(self.mount_all_list))
        # Mount /proc.
        procpath = os.path.join(CF.D.TGTSYS_ROOT, 'proc')
        if not os.path.isdir(procpath):
            os.makedirs(procpath)
        if not os.path.exists(os.path.join(procpath, 'cmdline')):
            ret, msg = mount_dev('proc', 'proc', mntdir=procpath)
        # Mount /sys
        syspath = os.path.join(CF.D.TGTSYS_ROOT, 'sys')
        if not os.path.isdir(syspath):
            os.makedirs(syspath)
        if not os.path.exists(os.path.join(syspath, 'block')):
            ret, msg = mount_dev('sysfs', 'sys', mntdir=syspath)

        _gen_fstab(self.mount_all_list)
#            ### TODO: do not need these copy ??
#            if CF.D.USEUDEV:
#                logger.i('Copy device files to target system.')
#                devdir = os.path.join(CF.D.TGTSYS_ROOT, 'dev')
#                if not os.path.isdir(devdir):
#                    os.makedirs(devdir)
#                os.system('cp -a /dev/* %s' % devdir)
        return  True, errmsg
        
    def umount_tgt_device(self):
        # Umount proc.
        errmsg = ''
        procdir = os.path.join(CF.D.TGTSYS_ROOT, 'proc')
        ret,msg = umount_dev(procdir, rmdir=False)
        if not ret:
            logger.w('Umount %s failed: %s\n' % (procdir, str(msg)))
        # Umount sys.
        sysdir = os.path.join(CF.D.TGTSYS_ROOT, 'sys')
        ret, msg = umount_dev(sysdir, rmdir=False)
        if not ret:
            logger.w('Umount %s failed: %s\n' % (sysdir, str(msg)))
    
        if os.path.exists('/tmpfs/debug/nomnttgt'):
            logger.d('TURN ON: nomnttgt\n')
            return True, ''
    
        # Copy the installation log into the target system.
        logdir = os.path.join(CF.D.TGTSYS_ROOT, 'var/log/MagicInstaller')
        os.system('mkdir -p %s' % logdir)
        os.system('cp /tmpfs/var/log/* %s' % logdir)
        os.system('cp /tmpfs/grub.* %s' % logdir)
    
        if os.path.exists('/tmpfs/debug/nomnttgt'):
            logger.d('TURN ON: nomnttgt\n')
            return True, errmsg
        self.mount_all_list.reverse()
        cnt = 0
        if self.progress_cb:
            self.progress_cb.set_step(cnt, len(self.mount_all_list))
        for (mntpoint, devfn, fstype) in self.mount_all_list:
            if fstype in ('linux-swap', 'linux-swap(v1)'):
                try:
                    isys.swapoff(devfn)
                except SystemError, em:
                    errmsg += _('swapoff(%s) failed: %s') % (devfn, str(em))
            else:
                for dev in self.mounted_devs:
                    if devfn == dev.get_dev():
                        if not dev.do_umount():
                            logger.w('Umount device %s Failed, but we continue', devfn)
                        break
            cnt = cnt + 1
            if self.progress_cb:
                self.progress_cb.set_step(cnt, len(self.mount_all_list))
            
        self.mounted_devs = []
        return  True, errmsg

@register.server_handler('long')
def install_prep(mia, operid, pkgsrc_devinfo, mount_all_list):
    '''
        Install all package prepare work.
        We should mount target system device, to prepare install packages.
        and mount disk which packages source is saved on.
        eg.
        ['/dev/sda10', 'ext4', 'MagicLinux-3.0-1.iso', 'MagicLinux/base'], 
        [('/', '/dev/sda3', 'ext4'), ('/home', '/dev/sda9', 'ext4'), ('', '/dev/sda7', 'linux-swap(v1)')]

    '''
    global dev_tgtsys # the target system devices.
    
    dev, fstype, bootiso_relpath, reldir = pkgsrc_devinfo

    logger.i('install_prep(%s, %s, %s, %s)\n' % (dev, fstype, bootiso_relpath, reldir))
    
    ############################## Mount Start #####################################            
    dev_tgtsys = MiDevice_TgtSys(mount_all_list)
    ret, msg = dev_tgtsys.mount_tgt_device() #### NOTE: carefully handle this device's mount.
    if not ret:
        msg = _('Mount target system devices Failed, install operate can not continue!!!\n %s') % msg
        logger.e(msg)
        dev_tgtsys = None
        return msg
    ############################## Mount Finished #####################################
    #--- This code is according to rpm.spec in rpm-4.2-0.69.src.rpm. ---
    # This code is specific to rpm.
    var_lib_rpm = os.path.join(CF.D.TGTSYS_ROOT, 'var/lib/rpm')
    if not os.path.isdir(var_lib_rpm):
        os.makedirs(var_lib_rpm)

    return  0

@register.server_handler('long')
def install_post(mia, operid, pkgsrc_devinfo, mount_all_list):
    global dev_tgtsys
    if dev_tgtsys:
        ret, msg = dev_tgtsys.umount_tgt_device()
        if not ret:
            msg = 'umount target system devices failed, but installation continue.\n%s' % msg
            logger.w(msg)
            dev_tgtsys = None
    return 0

@register.server_handler('long')
def install_disc_prep(mia, operid, dev, fstype, bootiso_relpath, reldir):
    '''
        Install each disc prepare work.
        We should mount each iso to prepare packages source(for disc).
        eg.
        '/dev/sda10', 'ext4', 'MagicLinux-3.0-1.iso', 'MagicLinux/base'

    '''
    logger.i('install_disc_prep(%s, %s, %s, %s)\n' % \
          (dev, reldir, fstype, bootiso_relpath))
    ############################## Mount Start #####################################
    CF.S.pkg_res_dev_hd = MiDevice(dev, fstype)
    if not CF.S.pkg_res_dev_hd.do_mount(): #### NOTE: carefully handle this device's mount.
        msg = _('Mount device %s Failed, install operate can not continue') % dev_hd.get_dev()
        logger.e(msg)
        return msg
        
    if bootiso_relpath:
        # an iso file on harddisk
        CF.S.pkg_res_dev_iso = MiDevice(CF.S.pkg_res_dev_hd.get_file_path(bootiso_relpath), 'iso9660')
        if not CF.S.pkg_res_dev_iso.do_mount(): #### NOTE: carefully handle this device's mount.
            CF.S.pkg_res_dev_hd.do_umount()
            CF.S.pkg_res_dev_hd = None
            msg = _('Mount device %s Failed, install operate can not continue!!!') % CF.S.pkg_res_dev_iso.get_dev()
            logger.e(msg)
            CF.S.pkg_res_dev_iso = None
            return msg
            
    ############################## Mount Finished #####################################
    return  0

@register.server_handler('long')
def install_disc_post(mia, operid, dev, fstype, bootiso_relpath, reldir):
    '''
        Install each disc post work.
        We should umount each iso and hard disk.
        eg.
        '/dev/sda10', 'ext4', 'MagicLinux-3.0-1.iso', 'MagicLinux/base'
    '''
    logger.i('install_disc_post(%s, %s, %s, %s)\n' % \
          (dev, fstype, reldir, bootiso_relpath))
    ################################ Umount Start #####################################
    if dev != CF.S.pkg_res_dev_hd.get_dev():
        msg = _('Error: previous use device %s, this time umount device %s, both should be equal, the install operate can not continue!!!') % (dev_hd.get_dev(), dev)
        logger.e(msg)
        return msg
    if CF.S.pkg_res_dev_iso:
        if not CF.S.pkg_res_dev_iso.do_umount():
            msg = _('Umount previous iso %s Failed, install operate can not continue!!!') % CF.S.pkg_res_dev_iso.get_dev()
            logger.e(msg)
            return msg
        CF.S.pkg_res_dev_iso = None
    if CF.S.pkg_res_dev_hd:
        if not CF.S.pkg_res_dev_hd.do_umount():
            msg = _('Umount previous iso %s Failed, install operate can not continue!!!') % dev_hd.get_dev()
            logger.e(msg)
            return msg
        if CF.S.pkg_res_dev_hd.get_fstype() == 'iso9660':
            # Eject the cdrom after used.
            try:
                #cdfd = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
                #isys.ejectcdrom(cdfd) # TODO: ejectcdrom use other method
                os.system('eject')
                #os.close(cdfd)
            except Exception, errmsg:
                logger.e('Eject(%s) failed: %s' % \
                            (dev, str(errmsg)))
                return str(errmsg)
        CF.S.pkg_res_dev_hd = None
    
    ################################ Umount Finished #####################################
    return  0

if __name__ == '__main__':
    TEST_MOUNT_ISO = False
    TEST_PROBE_ALL_DISC = True
    TEST_GEN_FSTAB = False
    TEST_MOUNT_TGTSYS = False
    def print_ret(ret, name=None):
        if name:
            print '=============== %s ================' % name
        else:
            print '==================================='
        print ret
        if name:
            print '=============== %s ================' % name
        else:
            print '==================================='
            
    from mi.server.utils import FakeMiactions
    mia = FakeMiactions()
    operid = 999
    def test_probe_all_disc():
        #ret = probe_all_disc(mia, operid, '/dev/sda10', 'ext4', 'MagicLinux-3.0-1.iso', 'MagicLinux/base', ['nss-softokn-freebl-3.13.3-1mgc30.i686.rpm'])
        ret = probe_all_disc(mia, operid, '/dev/sda10', 'ext4', 'MagicLinux-3.0-1.iso', 'MagicLinux/base', ['glibc-common-2.15-32mgc30.i686.rpm'])
        print 'TEST_PROBE_ALL_DISC RESULT: '
        print ret
        ### RESULT: probe_all_disc return result is : [('MagicLinux-3.0-1.iso', 'MagicLinux/base/nss-softokn-freebl-3.13.3-1mgc30.i686.rpm')]
        
    class MockProgress_CB():
        def set_step(self, step, total):
            print 'set_step %s / %s' % (step, total)
    
    if TEST_PROBE_ALL_DISC:
        test_probe_all_disc()
    if TEST_MOUNT_ISO:
        pkgsrc_devinfo = ['/dev/sda10', 'ext4', 'MagicLinux-3.0-1.iso', 'MagicLinux/base'] 
        mount_all_list = [('/', '/dev/sda3', 'ext4'), ('/home', '/dev/sda9', 'ext4'), ('', '/dev/sda7', 'linux-swap(v1)')]
        ret = install_prep(mia, operid, pkgsrc_devinfo, mount_all_list)
        print_ret(ret, 'install_prep')
        
        ret = install_disc_prep(mia, operid, *pkgsrc_devinfo)
        print_ret(ret, 'install_disc_prep')
        
        ret = install_disc_post(mia, operid, *pkgsrc_devinfo)
        print_ret(ret, 'install_disc_post')
        
        ret = install_post(mia, operid, pkgsrc_devinfo, mount_all_list)
        print_ret(ret, 'install_post')
        
    if TEST_GEN_FSTAB:
        print _gen_fstab([('/', '/dev/sda3', 'ext4'), ('/home', '/dev/sda9', 'ext4'), ('', '/dev/sda7', 'linux-swap(v1)')])
    if TEST_MOUNT_TGTSYS:
        tgtsys_obj = MiDevice_TgtSys([('/', '/dev/sda3', 'ext4'), ('/home', '/dev/sda9', 'ext4'), ('', '/dev/sda7', 'linux-swap(v1)')], MockProgress_CB())
        ret, msg = tgtsys_obj.mount_tgt_device()
        print_ret([ret, msg], 'mount return')
        
        ret, msg = tgtsys_obj.umount_tgt_device()
        print_ret([ret, msg], 'umount return')
        