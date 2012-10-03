import os, tarfile
from mi.server.utils import logger, CF, _

class CBFileObj(file):
    def __init__(self, filepath, data):
        self.progress_cb, self.total_size = data
        file.__init__(self, filepath)
        
    def read(self, size):
        self.progress_cb.set_step(self.tell(), self.total_size)
        return file.read(self, size)

class InstallTar(object):
    def __init__(self, tgtsys_root):
        self.tgtsys_root = tgtsys_root
        
    def _pre_pkg(self, pkgpath):
        return 0

    def _post_pkg(self, pkgpath):
        return 0
    
    def install_pre(self):
        return 0
    
    def install_post(self):
        return 0
    
    def _install(self, pkgpath, progress_cb):
        try:
            tar_size = os.path.getsize(pkgpath)
        except:
            errstr = _('Faild on get tar pakcage size "%s"') % (pkgpath, )
            logger.e(errstr)
            return errstr
        
        try:
            tarobj = tarfile.open(fileobj=CBFileObj(pkgpath, (progress_cb, tar_size)))
        except:
            errstr = _('Faild on create tarfile object on file "%s" size"%d"\n') % (pkgpath, tar_size)
            logger.e(errstr)
            return errstr
        
        try:
            tarobj.extractall(path=self.tgtsys_root)
        except:
            if tarobj:
                tarobj.close()
            errstr = _('Faild on extract file "%s" size"%d" to directory "%s"\n') % (pkgpath, tar_size, self.tgtsys_root)
            logger.e(errstr)
            return errstr
        
        try:
            tarobj.close()
        except:
            logger.w('Close tar pakcage failed path %s size %s' % (pkgpath, tar_size))
            
        return 0
    
    def install(self, pkgpath, progress_cb):
        ret = self._pre_pkg(pkgpath)
        if ret != 0:
            return 'PRE_PKG Failed %s' % ret
        ret = self._install(pkgpath, progress_cb)
        if ret != 0:
            return 'INSTALL Failed %s' % ret
        ret = self._post_pkg(pkgpath)
        if ret != 0:
            return 'POST_PKG Failed %s' % ret
        return 0

if __name__ == '__main__':
    pkglist = [(False, 'tests/data/tar_pkg.tar.bz2', True, True),
               (True, 'tests/data/num_util.tar.gz', True, True),
               ]

    class Mia(object):
        def set_step(self, stepid, step, total):
            print 'stepid %s step %s total %s' % (stepid, step, total)
            
    class Progress_CB(object):
        def __init__(self, mia, operid):
            self.mia = mia
            self.operid = operid
            
        def set_step(self, step, total):
            self.mia.set_step(self.operid, step, total)
    
    mia = Mia()
    operid = 0
    progress_cb = Progress_CB(mia, operid)
    
    inst_h = InstallTar(CF.D.TGTSYS_ROOT)
    inst_h.install_pre()
    
    for pkg in pkglist:
        if pkg[0]:
            ret = inst_h.install(pkg[1], progress_cb)
            if ret != 0:
                print 'install failed pkg %s %s' % (str(pkg), ret)
            else:
                print 'install success pkg %s %s' % (str(pkg), ret)

    inst_h.install_post()
    