#!/usr/bin/python
import os, glob, sys, syslog
import rpm, tarfile, time
from mi import isys, getdev #@UnresolvedImport
from mi.utils.common import mount_dev, umount_dev, run_bash, cdrom_available
from mi.server.utils.decorators import probe_cache
from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()

from mi.utils.miregister import MiRegister
register = MiRegister()

from mi.server.utils import logger
dolog = logger.info

cur_rpm_fd = 0
ts = None

# If we use use_noscripts we should open the option --noscripts in rpm command,
# and then we will do some configuration in instpkg_post.
use_noscripts = False
# if we not use_noscripts option, when package accept a noscripts parameter during
# install, it will also use --noscripts option to avoid run pre_install and
# post_install scripts, run these scripts in instpkg_post at last(same as use_noscripts).
noscripts_pkg_list = []
noscripts_log = '/var/log/mi/run_noscripts.log'
tmp_noscripts_dir = 'tmp/MI_noscripts'

installmode = 'rpminstallmode'
rpmdb = 'rpmdb.tar.bz2'
etctar = 'etc.tar.bz2'
etc_script = 'etc_install.sh'
tmp_config_dir = 'tmp/MI_configure'

dev_hd = None # the harddisk device where save packages.
dev_iso = None # the iso where save pkgs.
dev_tgt = None # the target system device.

class MiDevice(object):
    def __init__(self, blk_path, fstype, mntdir = ''):
        self.blk_path = blk_path
        self.fstype = fstype
        self.has_mounted = False
        self.mntdir = mntdir
        self.mntdir_fixed = self.mntdir and True or False
        self.loopmntdir = os.path.join(CF.D.MNT_ROOT, CF.D.ISOLOOP)
        
    def do_mount(self):
        if self.has_mounted: return True
        if not self.blk_path: logger.e('MiDevice.do_mount block path is "%s" ' % self.blk_path); return False
        # Priority to treat iso virtual device
        if self.fstype == 'iso9660':
            if not cdrom_available(self.blk_path):
                logger.w('MiDevice.do_mount %s type device "%s" cannot be used\n' % (self.fstype, self.blk_path))
                return False
            else:
                isopath = self.blk_path
                mountdir = self.mntdir_fixed and self.mntdir or self.loopmntdir
                ret, errmsg = mount_dev('iso9660', isopath, mountdir, flags='loop')
                if not ret:
                    logger.e("LoMount %s on %s as %s failed: %s" %  (isopath, mountdir, 'iso9660', str(errmsg)))
                    return False
                else:
                    if not self.mntdir_fixed: self.mntdir = self.loopmntdir
                    self.has_mounted = True
                    return True
                    
        # Then treat Harddisk Device
        if not self.mntdir_fixed:
            ret, mntdir = mount_dev(self.fstype, self.blk_path)
        else:
            ret, mntdir = mount_dev(self.fstype, self.blk_path, self.mntdir)
        if not ret:
            logger.e("MiDevice.do_mount Mount %s on %s as %s failed: %s" % \
                          (self.blk_path, mntdir, self.fstype, str(mntdir)))
            return False
        else:
            if not self.mntdir_fixed: self.mntdir = mntdir
            self.has_mounted = True
            return True
            
    def get_file_path(self, relpath):
        ''' only use after mount and before umount '''
        return os.path.join(self.mntdir, relpath)
        
    def get_mountdir(self):
        return self.mntdir
    
    def do_umount(self):
        if not self.has_mounted: return True
        ret, errmsg = umount_dev(self.mntdir)
        if not ret:
            logger.e("MiDevice.do_umount UMount(%s) failed: %s" % (self.mntdir, str(errmsg))); return False
        else:
            self.has_mounted = False
            if not self.mntdir_fixed: self.mntdir = ''
            return True
            
    def get_dev(self):
        return self.blk_path
        
    def get_fstype(self):
        return self.fstype
        
    def iter_searchfiles(self, fs_lst, pathes):
        opt_mount = True
        if self.has_mounted:
            opt_mount = False
        if opt_mount:
            if not self.do_mount(): return
        for p in pathes:
            for fn in fs_lst:
                pp = os.path.join(self.mntdir, p, fn)
                if os.access(pp, os.R_OK):
                    yield pp, p
        if opt_mount:
            self.do_umount()

@register.server_handler('long', 'pkgarr_probe')
@probe_cache('pkgarr')
def pkgarr_probe(mia, operid):
    logger.i("pkgarr_probe starting...")
    def probe_position(localfn, pos_id, new_device, fstype, reldir, isofn):
        dolog('probe_position: %s, %s, %s, %s, %s, %s' % (localfn, pos_id, new_device, fstype, reldir, isofn))
        if not os.path.exists(localfn):
            return None
        try:
            execfile(localfn)
        except Exception, errmsg:
            logger.e("Load %s failed(%s)." % (localfn, str(errmsg)))
            return None
        remotefn = 'allpa/%s.%d.%s' % (os.path.basename(new_device), pos_id, os.path.basename(localfn))
        dolog('tftpc update %s to remote %s...' % (localfn, remotefn))
#        cli.put(localfn, remotefn)
        os.system('tftp 127.0.0.1 69 -p -l %s -r %s' % (localfn, remotefn))
        return [remotefn, new_device, fstype, reldir, isofn]
        # The format like ('allpa/hdc.1.pkgarr.py', '/dev/hdc', 'iso9660', 'MagicLinux/base', '')
        # ['allpa/sda6.100.pkgarr.py', '/dev/sda6', 'ext3', 'MagicLinux/base', 'MagicLinux-3.0-1.iso']
    mia.set_step(operid, 0, -1)
    #cli = tftpc.TFtpClient()
    #cli.connect('127.0.0.1')
    result = []
    
    all_drives = getdev.get_part_info(getdev.CLASS_CDROM | getdev.CLASS_HD)
    #map(lambda cd: all_drives.append((os.path.join('/dev', cd.device),
    #                                  'iso9660',
    #                                  os.path.join('/dev', cd.device))),
    #                                  cdlist)
    dolog('all_drives: %s' % all_drives)
    pos_id = -1
    for k, value in all_drives.items():
        devpath = value['devpath']
        fstype = value['fstype']
        if not CF.D.FSTYPE_MAP.has_key(fstype):
            continue
        if CF.D.FSTYPE_MAP[fstype][0] == '':
            continue
        midev = MiDevice(devpath, CF.D.FSTYPE_MAP[fstype][0])
        for f, reldir in midev.iter_searchfiles([CF.D.PKGARR_FILE, CF.D.BOOTCDFN], CF.D.PKGARR_SER_HDPATH):
            if f.endswith('iso'):
                midev_iso = MiDevice(f, 'iso9660')
                for pkgarr, relative_dir in midev_iso.iter_searchfiles([CF.D.PKGARR_FILE], CF.D.PKGARR_SER_CDPATH):
                    pos_id += 1
                    r = probe_position(pkgarr, 100 + pos_id,
                        devpath, CF.D.FSTYPE_MAP[fstype][0], relative_dir, CF.D.BOOTCDFN)
                    if r:
                        r[-1] = os.path.join(reldir, r[-1]) #### revise iso relative path
                        result.append(r)
            else:
                pos_id += 1
                r = probe_position(pkgarr, pos_id,
                    devpath, fstype, reldir, '')
                if r: result.append(r)
    
#    del(cli)
    logger.w("pkgarr_probe %s" % result)
    return result

@register.server_handler('long')
def probe_all_disc(mia, operid, device, devfstype, bootiso_relpath, pkgarr_reldir, disc_first_pkgs):
    '''
        probe the package from all disk
        bootiso_relpath is the first iso path relative path of device /
        pkgarr_reldir is the relative directory path of pkgarr.py of device / OR iso dir /
    '''
    dolog('probe_all_disc(%s, %s, %s, %s, %s)\n' % \
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

    dolog('probe_all_disc return result is : %s\n' % str(result))
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
def instpkg_prep(mia, operid, pkgsrc_devinfo, instmode, tgtsys_devinfo):
    '''
        Install all package prepare work.
        We should mount target system device, to prepare install packages.
        and mount disk which packages source is saved on.
    '''
    ######### TODO: !!! there to get get get
    # Set the package install mode.
    global installmode
    
    global dev_hd # the harddisk device where save packages.
    global dev_iso # the iso where save pkgs.
    global dev_tgt # the target system devices.
    
    dev, fstype, bootiso_relpath, reldir = pkgsrc_devinfo
    
    installmode = instmode
    if CF.D.PKGTYPE == 'rpm': dolog('InstallMode: Rpm Packages %s\n' % installmode)
    elif CF.D.PKGTYPE == 'tar': dolog('InstallMode: Tar Packages\n')
    dolog('instpkg_prep(%s, %s, %s, %s)\n' % (dev, fstype, bootiso_relpath, reldir))
    
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
    dolog('instpkg_disc_prep(%s, %s, %s, %s)\n' % \
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
    if installmode == 'copyinstallmode':
        # determine the rpmdb.tar.bz2 and etc.tar.bz2. If exist copy it to tmp_config_dir in target system.
        rpmpkgdir = os.path.dirname(first_pkg)
        rpmdb_abs = os.path.join(rpmpkgdir, rpmdb)
        etctar_abs = os.path.join(rpmpkgdir, etctar)
        tgt_tmp_config_dir = os.path.join(CF.D.TGTSYS_ROOT, tmp_config_dir)
        if not os.path.exists(tgt_tmp_config_dir):
            os.makedirs(tgt_tmp_config_dir)
        if os.path.exists(rpmdb_abs):
            ret = os.system('cp %s %s' % (rpmdb_abs, os.path.join(tgt_tmp_config_dir, rpmdb)))
            if ret != 0:
                dolog('copy %s to target system failed.\n' % rpmdb)
            else:
                dolog('copy %s to target system successfully.\n' % rpmdb)
        if os.path.exists(etctar_abs):
            ret = os.system('cp %s %s' % (etctar_abs, os.path.join(tgt_tmp_config_dir, etctar)))
            if ret != 0:
                dolog('copy %s to target system failed.\n' % rpmdb)
            else:
                dolog('copy %s to target system successfully.\n' % rpmdb)
            
    dolog('instpkg_disc_post(%s, %s, %s, %s, %s)\n' % \
          (dev, fstype, reldir, bootiso_relpath, first_pkg))
    # We don't know which package start the minilogd but it
    # will lock the disk, so it must be killed.
    if os.system('/usr/bin/killall minilogd') == 0:
        time.sleep(2)
        
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
def instpkg_post(mia, operid, dev, reldir, fstype):
    global noscripts_pkg_list
    if installmode == 'rpminstallmode' and noscripts_pkg_list:
        # we will execute all the pre_in and post_in scripts there, if we use
        # the --noscripts option during rpm installation
        dolog('Execute Pre Post Scripts:\n\t%s\n' % str(noscripts_pkg_list))
        def run_pre_post_in_script(TMP):
            def get_pkg_name(pkgrpm):
                pkg = os.path.basename(pkgrpm)
                pkgname = ''
                try:
                    pkgname = pkg[:pkg.rindex('-')]
                    pkgname = pkg[:pkgname.rindex('-')]
                except ValueError, e:
                    return pkg
                return pkgname
            def write_script(script_cmd, script_file, mode='w'):
                tfd = open(script_file, mode)
                tfd.write(script_cmd)
                tfd.close()
            def excute_pre_post(h):
                pkgnvr = "%s-%s-%s" % (h['name'],h['version'],h['release'])
                script_dir = os.path.join(CF.D.TGTSYS_ROOT, tmp_noscripts_dir)
                scripts = []
                if h[rpm.RPMTAG_PREIN]: #@UndefinedVariable
                    script_name = "%s.preinstall.sh" % pkgnvr
                    script_path = os.path.join(script_dir, script_name)
                    write_script(h[rpm.RPMTAG_PREIN], script_path) #@UndefinedVariable
                    scripts.append(script_name)
                if h[rpm.RPMTAG_POSTIN]: #@UndefinedVariable
                    script_name = "%s.postinstall.sh" % pkgnvr
                    script_path = os.path.join(script_dir, script_name)
                    write_script(h[rpm.RPMTAG_POSTIN], script_path) #@UndefinedVariable
                    scripts.append(script_name)
                for script_name in scripts:
                    spath = os.path.join('/', tmp_noscripts_dir, script_name)
                    write_script("**%s\n" % script_name, noscripts_log, 'a')  # do log
                    ret = os.system("/usr/sbin/chroot %s /bin/sh %s  2>&1 >> %s" % (CF.D.TGTSYS_ROOT, spath, noscripts_log))
                    if ret != 0:
                        err_msg = 'Error run scripts(noscripts) in %s-%s-%s\n' \
                                % (h['name'],h['version'],h['release'])
                        dolog(err_msg)
                        write_script(err_msg, noscripts_log, 'a')   # do log
            write_script('Execute Pre Post Scripts:\n\t%s\n' % str(noscripts_pkg_list), noscripts_log, 'a')  # do log            
            script_dir = os.path.join(CF.D.TGTSYS_ROOT, tmp_noscripts_dir)
            if not os.path.exists(script_dir):
                os.makedirs(script_dir)
            ts_m = rpm.TransactionSet(CF.D.TGTSYS_ROOT)
            for pkg in noscripts_pkg_list:
                pkgname = get_pkg_name(pkg)
                mi = ts_m.dbMatch('name', pkgname)
                for h in mi:
                    if h['name'] == pkgname:
                        excute_pre_post(h)
            noscripts_pkg_list = []

        run_pre_post_in_script(CF.D.TGTSYS_ROOT)

    if installmode == 'copyinstallmode':
        tgt_tmp_config_dir = os.path.join(CF.D.TGTSYS_ROOT, tmp_config_dir)
        rpmdb_abs = os.path.join(tgt_tmp_config_dir, rpmdb)
        etctar_abs = os.path.join(tgt_tmp_config_dir, etctar)
        if os.path.exists(rpmdb_abs):
            ret = os.system('tar -xjf %s -C %s' % (rpmdb_abs, CF.D.TGTSYS_ROOT))
            if ret != 0:
                dolog('ERROR: Extract %s from target system %s to target system Failed.\n' \
                %(rpmdb, rpmdb_abs[len(CF.D.TGTSYS_ROOT):]))
            os.system('rm -r %s' % rpmdb_abs)
        else:
            dolog('Warning: cannot find the needed file %s.\n' % rpmdb_abs[len(CF.D.TGTSYS_ROOT):])
        if os.path.exists(etctar_abs):
            ret = os.system('tar -xjf %s -C %s' % (etctar_abs, os.path.join(CF.D.TGTSYS_ROOT, tmp_config_dir)))
            if ret != 0:
                dolog('ERROR: Extract %s from target system %s to target system Failed.\n' \
                %(etctar, etctar_abs[len(CF.D.TGTSYS_ROOT):]))
        else:
            dolog('Warning: cannot find the needed file %s.\n' % etctar_abs[len(CF.D.TGTSYS_ROOT):])
        # do chroot and excute the etc_install.sh
        ret = os.system('/usr/sbin/chroot %s /%s %s' \
                % (CF.D.TGTSYS_ROOT, os.path.join(tmp_config_dir, etc_script), tmp_config_dir))
        if ret != 0:
            dolog('ERROR: run %s failed.\n' % os.path.join(tmp_config_dir, etc_script))
        else:
            dolog('Run %s successfully.\n' % os.path.join(tmp_config_dir, etc_script))
        os.system('rm -r %s' % os.path.join(CF.D.TGTSYS_ROOT, tmp_config_dir))
        
    global ts
    if ts is not None:
        dolog('Close TransactionSet\n')
        ts.closeDB()
        ts = None
    dolog('instpkg_post(%s, %s, %s)\n' % (dev, reldir, fstype))
    if fstype == 'iso9660':
        return  0  # It is ok for CDROM installation.
    mia.set_step(operid, 0, -1) # Sync is the long operation.
#    if mntxxxpoint != 0: #### TODO; !!!!!UNKNOWN!!!!!!
#        mntdir = os.path.join(CF.D.TGTSYS_ROOT, mntxxxpoint)     ####TODO
#    else:
#        mntdir = os.path.join(CF.D.MNT_ROOT, os.path.basename(dev))
#        ret, errmsg = umount_dev(mntdir)
#        if not ret:
#            logger.e('UMount(%s) failed: %s' % \
#                          (mntdir, str(errmsg)))
#            return str(errmsg)
    try:
        isys.sync()
    except Exception, errmsg:
        logger.e('sync failed: %s' % str(errmsg))
        return str(errmsg)
    return  0
    
######################   Install package below code    #########################
# Now package_install support rpm only.
@register.server_handler('long')
def rpm_installcb(what, bytes, total, h, data):
    global  cur_rpm_fd
    (mia, operid) = data
    if what == rpm.RPMCALLBACK_INST_OPEN_FILE: #@UndefinedVariable
        cur_rpm_fd = os.open(h, os.O_RDONLY)
        return  cur_rpm_fd
    elif what == rpm.RPMCALLBACK_INST_CLOSE_FILE: #@UndefinedVariable
        os.close(cur_rpm_fd)
    elif what == rpm.RPMCALLBACK_INST_PROGRESS: #@UndefinedVariable
        mia.set_step(operid, bytes, total)
        
class CBFileObj(file):
    def __init__(self, filepath, data):
        self.mia, self.operid, self.total_size = data
        file.__init__(self, filepath)
    def read(self, size):
        self.mia.set_step(self.operid, self.tell(), self.total_size)
        return file.read(self, size)

@register.server_handler('long')
def package_install(mia, operid, pkgname, firstpkg, noscripts):
    use_ts = False
    global dev_hd
    global dev_iso
    pkgpath = os.path.join(os.path.dirname(firstpkg), pkgname)
    pkgpath = dev_iso and dev_iso.get_file_path(pkgpath) or dev_hd.get_file_path(pkgpath)
    #dolog('pkg_install(%s, %s)\n' % (pkgname, str(pkgpath)))
    
    def do_ts_install():
        global ts
        if ts is None:
            dolog('Create TransactionSet\n')
            ts = rpm.TransactionSet(CF.D.TGTSYS_ROOT)
            ts.setProbFilter(rpm.RPMPROB_FILTER_OLDPACKAGE | #@UndefinedVariable
                             rpm.RPMPROB_FILTER_REPLACENEWFILES | #@UndefinedVariable
                             rpm.RPMPROB_FILTER_REPLACEOLDFILES | #@UndefinedVariable
                             rpm.RPMPROB_FILTER_REPLACEPKG) #@UndefinedVariable
            ts.setVSFlags(~(rpm.RPMVSF_NORSA | rpm.RPMVSF_NODSA)) #@UndefinedVariable
            
            # have been removed from last rpm version
            #ts.setFlags(rpm.RPMTRANS_FLAG_ANACONDA)
        try:
            rpmfd = os.open(pkgpath, os.O_RDONLY)
            hdr = ts.hdrFromFdno(rpmfd)
            ts.addInstall(hdr, pkgpath, 'i')
            os.close(rpmfd)
            # Sign the installing pkg name in stderr.
            print >>sys.stderr, '%s ERROR :\n' % pkgname
            problems = ts.run(rpm_installcb, (mia, operid))
            if problems:
                dolog('PROBLEMS: %s\n' % str(problems))
                # problems is a list that each elements is a tuple.
                # The first element of the tuple is a human-readable string
                # and the second is another tuple such as:
                #    (rpm.RPMPROB_FILE_CONFLICT, conflict_filename, 0L)
                return  problems
        except Exception, errmsg:
            dolog('FAILED: %s\n' % str(errmsg))
            return str(errmsg)
            
    def do_bash_rpm_install():
        global noscripts_pkg_list
        global use_noscripts
        mia.set_step(operid, 1, 1)
            
        try:
            cmd = 'rpm'
            argv = ['-i', '--noorder', # '--nosuggest', # on ubuntu platform rpm do not have --nosuggest parameter
                    '--force','--nodeps',
                    '--ignorearch',
                    '--root', CF.D.TGTSYS_ROOT,
                    pkgpath,
                ]
            if use_noscripts or noscripts:
                argv.append('--noscripts')
                noscripts_pkg_list.append(pkgpath)

            #cmd_res = {'err':[], 'std': [], 'ret':0}   # DEBUG
            cmd_res = run_bash(cmd, argv)
            # Sign the installing pkg name in stderr
            if cmd_res['err']:
                # Ok the stderr will dup2 a log file, so we just out it on err screen
                print >>sys.stderr, '***INSTALLING %s:\n**STDERR:\n%s\n' \
                        %(pkgname, ''.join(cmd_res['err']))
            problems = cmd_res['ret']
            if problems:
                errormsg = ''.join(cmd_res['err'])
                message = 'PROBLEMS on %s: \n return code is %s error message is\n[%s]' \
                          % (pkgname, str(problems), errormsg)
                dolog(message)
                return  message
        except Exception, errmsg:
            dolog('FAILED on %s: %s\n' % (pkgname, str(errmsg)))
            return str(errmsg)
            
    def do_copy_install():
        mia.set_step(operid, 1, 1)
        try:
            cmd = 'cd %s && /usr/bin/rpm2cpio %s | /bin/cpio -dui --quiet' % (CF.D.TGTSYS_ROOT, pkgpath)
            problems = os.system(cmd)
            if problems:
                message = 'PROBLEMS on %s: \n return code is %s command is\n[%s]' \
                          % (pkgname, str(problems), cmd)
                dolog(message)
                return  message
        except Exception, errmsg:
            dolog('FAILED on %s: %s\n' % (pkgname, str(errmsg)))
            return str(errmsg)
            
    def do_tar_extract_install():
        tar_size = os.path.getsize(pkgpath)
        try:
            tarobj = tarfile.open(fileobj=CBFileObj(pkgpath, (mia, operid, tar_size)))
        except:
            errstr = 'Faild on create tarfile object on file "%s" size"%d"\n' % (pkgpath, tar_size)
            dolog(errstr)
            return errstr
        try:
            tarobj.extractall(path=CF.D.TGTSYS_ROOT)
        except:
            if tarobj:
                tarobj.close()
            errstr = 'Faild on extract file "%s" size"%d" to directory "%s"\n' % (pkgpath, tar_size, CF.D.TGTSYS_ROOT)
            dolog(errstr)
            return errstr
        try:
            tarobj.close()
        except:
            pass
        
    # Decide using which mode to install.
    ret = 'Nothing'
    if CF.D.PKGTYPE == 'rpm':     # In the mipublic.py
        if installmode == 'rpminstallmode':
            if use_ts:
                # Use rpm-python module to install rpm pkg, but at this version it is very slowly.
                ret = do_ts_install()
            else:
                # Because I can not use rpm-python module to install quickly.
                # So use the bash mode to install the pkg, it is very fast.
                # If you can use rpm-python module install pkg quickly, you can remove it.
                ret = do_bash_rpm_install()
        elif installmode == 'copyinstallmode':
            # Use rpm2cpio name-ver-release.rpm | cpio -diu to uncompress the rpm files to target system.
            # Then we will do some configuration in instpkg_post.
            ret = do_copy_install()
    elif CF.D.PKGTYPE == 'tar':
        ret = do_tar_extract_install()
    if ret:
        return ret
    else:
        return 0

class MiaTest(object):
    def __init__(self):
        from mi.server.utils import FakeMiactions
        self.mia = FakeMiactions()
        self.operid = 999
        
class Test(MiaTest):
    def __init__(self):
        MiaTest.__init__(self)
        
    def test_pkgarr_probe(self):
        hdpartlist = [
            ['/dev/sda1', 'ntfs', '/dev/sda1'], 
            ['/dev/sda2', 'ntfs', '/dev/sda2'], 
            ['/dev/sda5', 'linux-swap(v1)', '/dev/sda5'], 
            ['/dev/sda6', 'ext3', '/dev/sda6'], 
            ['/dev/sda7', 'ext4', '/dev/sda7'], 
            ['/dev/sda8', 'ntfs', '/dev/sda8'], ]
        pkgarr_probe(self.mia, self.operid)
    
    def test_probe_all_disc(self):
        probe_all_disc(self.mia, self.operid, '/dev/sda10', 'ext4', 'MagicLinux-3.0-1.iso', 'MagicLinux/base', ['nss-softokn-freebl-3.13.3-1mgc30.i686.rpm'])
        ### RESULT: probe_all_disc return result is : [('MagicLinux-3.0-1.iso', 'MagicLinux/base/nss-softokn-freebl-3.13.3-1mgc30.i686.rpm')]
        
if __name__ == '__main__':
    test = Test()
    test.test_pkgarr_probe()
    #test.test_probe_all_disc()
    
    