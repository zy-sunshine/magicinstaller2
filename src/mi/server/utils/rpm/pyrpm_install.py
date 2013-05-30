import os, sys, rpm
from mi.server.utils import logger, CF
from mi.server.utils.rpm.version import get_pkg_name
import glob
def _rpm_installcb(what, bytes, total, h, data):
    global  cur_rpm_fd
    (progress_cb, ) = data
    if what == rpm.RPMCALLBACK_INST_OPEN_FILE: #@UndefinedVariable
        cur_rpm_fd = os.open(h, os.O_RDONLY)
        return  cur_rpm_fd
    elif what == rpm.RPMCALLBACK_INST_CLOSE_FILE: #@UndefinedVariable
        os.close(cur_rpm_fd)
    elif what == rpm.RPMCALLBACK_INST_PROGRESS: #@UndefinedVariable
        progress_cb.set_step(bytes, total)

class InstallRpm(object):
    def __init__(self, tgtsys_root):
        self.tgtsys_root = tgtsys_root
        self.ts = None
        
    def _pre_pkg(self, pkgpath):
        return 0

    def _post_pkg(self, pkgpath):
        return 0

    def install_pre(self):
        logger.i('Create TransactionSet\n')
        self.ts = rpm.TransactionSet(self.tgtsys_root)
        self.ts.setProbFilter(rpm.RPMPROB_FILTER_OLDPACKAGE | #@UndefinedVariable
                            rpm.RPMPROB_FILTER_REPLACENEWFILES | #@UndefinedVariable
                            rpm.RPMPROB_FILTER_REPLACEOLDFILES | #@UndefinedVariable
                            rpm.RPMPROB_FILTER_REPLACEPKG) #@UndefinedVariable
        self.ts.setVSFlags(~(rpm.RPMVSF_NORSA | rpm.RPMVSF_NODSA)) #@UndefinedVariable

        # have been removed from last rpm version
        #self.ts.setFlags(rpm.RPMTRANS_FLAG_ANACONDA)
        rpm.addMacro("__dbi_htconfig", #@UndefinedVariable
             "hash nofsync %{__dbi_other} %{__dbi_perms}")
        rpm.addMacro("__file_context_path", "%{nil}") #@UndefinedVariable
        var_lib_rpm = os.path.join(self.tgtsys_root, 'var/lib/rpm')
        if not os.path.isdir(var_lib_rpm):
            os.makedirs(var_lib_rpm)
        return 0
    
    def install_post(self):
        if self.ts is not None:
            logger.i('Close TransactionSet\n')
            self.ts.closeDB()
            self.ts = None
        return 0

    def _install(self, pkgpath, progress_cb):
        try:
            pkgname = get_pkg_name
            rpmfd = os.open(pkgpath, os.O_RDONLY)
            hdr = self.ts.hdrFromFdno(rpmfd)
            self.ts.addInstall(hdr, pkgpath, 'i')
            os.close(rpmfd)
            # Sign the installing pkg name in stderr.
            #print >>sys.stderr, '%s ERROR :\n' % pkgname
            problems = self.ts.run(_rpm_installcb, (progress_cb, ))
            if problems:
                logger.i('PROBLEMS: %s\n' % str(problems))
                # problems is a list that each elements is a tuple.
                # The first element of the tuple is a human-readable string
                # and the second is another tuple such as:
                #    (rpm.RPMPROB_FILE_CONFLICT, conflict_filename, 0L)
                return  problems
        except Exception, errmsg:
            logger.w('FAILED: %s\n' % str(errmsg))
            return str(errmsg)
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
    pkglist = [(False, '/home/zhangyang09/work/dist/RPMS.base/glibc-2.15-32mgc30.i686.rpm', True, True),
               (False, '/home/zhangyang09/work/dist/RPMS.base/bash-4.2.29-2mgc30.i686.rpm', True, False),
               (True, '/home/zhangyang09/work/dist/RPMS.base/libgcc-4.6.2-2mgc30.1.i686.rpm', True, True),
               (False, '/home/zhangyang09/work/dist/RPMS.base/filesystem-3-3mgc30.i686.rpm', True, False),
               ]
    pkglist = []
    for pkg in glob.glob('/home/zhangyang09/work/dist/RPMS.base/*.rpm'):
        pkglist.append((True, pkg, True, True))
    print len(pkglist)
    class Mia(object):
        def set_step(self, stepid, step, total):
            pass
            #print 'stepid %s step %s total %s' % (stepid, step, total)
            
    class Progress_CB(object):
        def __init__(self, mia, operid):
            self.mia = mia
            self.operid = operid
            
        def set_step(self, step, total):
            self.mia.set_step(self.operid, step, total)
    
    mia = Mia()
    operid = 0
    progress_cb = Progress_CB(mia, operid)
    
    inst_h = InstallRpm(CF.D.TGTSYS_ROOT)
    inst_h.install_pre()
    
    for pkg in pkglist:
        if pkg[0]:
            ret = inst_h.install(pkg[1], progress_cb)
            if ret != 0:
                print 'install failed pkg %s %s' % (str(pkg), ret)
            else:
                print 'install success pkg %s %s' % (str(pkg), ret)

    inst_h.install_post()
    