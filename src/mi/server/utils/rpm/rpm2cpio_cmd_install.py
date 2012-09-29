import os
from mi.server.utils import logger
class InstallRpm():
    def __init__(self):
        pass
    
    def _install(self):
        try:
            cmd = 'cd %s && /usr/bin/rpm2cpio %s | /bin/cpio -dui --quiet' % (CF.D.TGTSYS_ROOT, pkgpath)
            problems = os.system(cmd)
            if problems:
                message = 'PROBLEMS on %s: \n return code is %s command is\n[%s]' \
                          % (pkgname, str(problems), cmd)
                logger.i(message)
                return  message
        except Exception, errmsg:
            logger.i('FAILED on %s: %s\n' % (pkgname, str(errmsg)))
            return str(errmsg)
    def install(self, pkgpath):
        self.pre_script(pkgpath)
        self._install(pkgpath)
        self.post_script(pkgpath)
        
def pkg_post(mia, operid, dev, reldir, fstype):
    global noscripts_pkg_list
    tgt_tmp_config_dir = os.path.join(CF.D.TGTSYS_ROOT, tmp_config_dir)
    rpmdb_abs = os.path.join(tgt_tmp_config_dir, rpmdb)
    etctar_abs = os.path.join(tgt_tmp_config_dir, etctar)
    if os.path.exists(rpmdb_abs):
        ret = os.system('tar -xjf %s -C %s' % (rpmdb_abs, CF.D.TGTSYS_ROOT))
        if ret != 0:
            logger.i('ERROR: Extract %s from target system %s to target system Failed.\n' \
            %(rpmdb, rpmdb_abs[len(CF.D.TGTSYS_ROOT):]))
        os.system('rm -r %s' % rpmdb_abs)
    else:
        logger.i('Warning: cannot find the needed file %s.\n' % rpmdb_abs[len(CF.D.TGTSYS_ROOT):])
    if os.path.exists(etctar_abs):
        ret = os.system('tar -xjf %s -C %s' % (etctar_abs, os.path.join(CF.D.TGTSYS_ROOT, tmp_config_dir)))
        if ret != 0:
            logger.i('ERROR: Extract %s from target system %s to target system Failed.\n' \
            %(etctar, etctar_abs[len(CF.D.TGTSYS_ROOT):]))
    else:
        logger.i('Warning: cannot find the needed file %s.\n' % etctar_abs[len(CF.D.TGTSYS_ROOT):])
    # do chroot and excute the etc_install.sh
    ret = os.system('/usr/sbin/chroot %s /%s %s' \
            % (CF.D.TGTSYS_ROOT, os.path.join(tmp_config_dir, etc_script), tmp_config_dir))
    if ret != 0:
        logger.i('ERROR: run %s failed.\n' % os.path.join(tmp_config_dir, etc_script))
    else:
        logger.i('Run %s successfully.\n' % os.path.join(tmp_config_dir, etc_script))
    os.system('rm -r %s' % os.path.join(CF.D.TGTSYS_ROOT, tmp_config_dir))
        

    logger.i('instpkg_post(%s, %s, %s)\n' % (dev, reldir, fstype))
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

    return  0
    