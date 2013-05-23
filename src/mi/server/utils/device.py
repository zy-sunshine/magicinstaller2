import os
from mi.utils.common import mount_dev, umount_dev, run_bash, cdrom_available
from mi.server.utils import logger, CF
import time
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
        for t in range(3): # try 3 time, because some udisk program will hold on disk, when disk mount. umount action can not so quickly.
            ret, errmsg = umount_dev(self.mntdir)
            if ret:
                break
            else:
                time.sleep(1)
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
        
    def iter_searchfiles(self, fs_lst, paths):
        '''
            auto mount deivce, and search file list (fs_lst) in these paths (paths)
            RETURN:
                (absolute_path, reltive_dir)
                file absolute path(p) and which path find it(pp)
        '''
        opt_mount = True
        if self.has_mounted:
            opt_mount = False
        if opt_mount:
            if not self.do_mount(): return
        for p in paths:
            p = p.strip('/')
            for fn in fs_lst:
                pp = os.path.join(self.mntdir, p, fn)
                if os.access(pp, os.R_OK):
                    yield pp, p
        if opt_mount:
            self.do_umount()
