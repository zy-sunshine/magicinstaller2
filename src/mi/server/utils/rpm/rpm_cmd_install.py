import os, sys, rpm
from mi.utils.common import run_bash
from mi.server.utils import logger, CF
from mi.server.utils.rpm.version import get_pkg_name

class InstallRpm():
    def __init__(self):
        self.noscripts_pkg_list = []
        self.use_noscripts = True
        self.tmp_noscripts_dir = 'tmp/MI_noscripts'
        
        # If we use use_noscripts we should open the option --noscripts in rpm command,
        # and then we will do some configuration in instpkg_post.
        self.use_noscripts = False
        self.not_pre_post_script = False
        # if we not use_noscripts option, when package accept a noscripts parameter during
        # install, it will also use --noscripts option to avoid run pre_install and
        # post_install scripts, run these scripts in instpkg_post at last(same as use_noscripts).
        self.noscripts_pkg_list = []
        self.noscripts_log = '/var/log/mi/run_noscripts.log'
        if not os.path.exists(os.path.dirname(self.noscripts_log)):
            os.mkdir(os.path.dirname(self.noscripts_log))
            
        self.tgtsys_root = CF.D.TGTSYS_ROOT
        
    def _install(self, pkgpath, noscripts, not_pre_post_script):
        pkgname = get_pkg_name(pkgpath)
        try:
            cmd = 'rpm'
            argv = ['-i', '--noorder', # '--nosuggest', # on ubuntu platform rpm do not have --nosuggest parameter
                    '--force','--nodeps',
                    '--ignorearch',
                    '--root', CF.D.TGTSYS_ROOT,
                    pkgpath,
                ]
            if self.use_noscripts or noscripts:
                argv.append('--noscripts')
                self.noscripts_pkg_list.append(pkgpath)
    
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
                logger.i(message)
                return  message
        except Exception, errmsg:
            logger.i('FAILED on %s: %s\n' % (pkgname, str(errmsg)))
            return str(errmsg)
        return 0
    
    def _pre_pkg(self, pkgpath, noscripts, not_pre_post_script):
        return 0
    
    def _post_pkg(self, pkgpath, noscripts, not_pre_post_script):
        ### TODO Because this method to dump post script is not a valid bash script, it is like:
        # posix.symlink("../run", "/var/run")
        # posix.symlink("../run/lock", "/var/lock")
        # I do not know, may be it is the rpm inter language to create a link.
        # It happend in filesystem-3-3mgc30.i686.rpm please check.
        
        return -1
        # we will execute all the pre_in and post_in scripts there, if we use
        # the --noscripts option during rpm installation
        logger.i('Execute Pre Post Scripts:\n\t%s\n' % str(self.noscripts_pkg_list))
        
        if not self.noscripts_pkg_list:
            return 0
        if self.not_pre_post_script or not_pre_post_script:
            return 0
        def write_script(script_cmd, script_file, mode='w'):
            tfd = open(script_file, mode)
            tfd.write(script_cmd)
            tfd.close()
        def excute_pre_post(h):
            pkgnvr = "%s-%s-%s" % (h['name'],h['version'],h['release'])
            script_dir = os.path.join(self.tgtsys_root, self.tmp_noscripts_dir)
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
                spath = os.path.join('/', self.tmp_noscripts_dir, script_name)
                write_script("**%s\n" % script_name, self.noscripts_log, 'a')  # do log
                ret = os.system("/usr/sbin/chroot %s /bin/sh %s  2>&1 >> %s" % (self.tgtsys_root, spath, self.noscripts_log))
                if ret != 0:
                    err_msg = 'Error run scripts(noscripts) in %s-%s-%s\n' \
                            % (h['name'],h['version'],h['release'])
                    logger.i(err_msg)
                    write_script(err_msg, self.noscripts_log, 'a')   # do log
                    return ret
            return 1
        write_script('Execute Pre Post Scripts:\n\t%s\n' % str(self.noscripts_pkg_list), self.noscripts_log, 'a')  # do log            
        script_dir = os.path.join(self.tgtsys_root, self.tmp_noscripts_dir)
        if not os.path.exists(script_dir):
            os.makedirs(script_dir)
        ts_m = rpm.TransactionSet(self.tgtsys_root)
        for pkg in self.noscripts_pkg_list:
            pkgname = get_pkg_name(pkg)
            mi = ts_m.dbMatch('name', pkgname)
            for h in mi:
                if h['name'] == pkgname:
                    ret = excute_pre_post(h)
                    if ret != 0:
                        # Error
                        return ret
                    
        self.noscripts_pkg_list = []
        return 0
    
    def install(self, pkgpath, noscripts=False, not_pre_post_script=False):
        ret = self._pre_pkg(pkgpath, noscripts, not_pre_post_script)
        if ret != 0:
            return 'PRE_PKG Failed %s' % ret
        ret = self._install(pkgpath, noscripts, not_pre_post_script)
        if ret != 0:
            return 'INSTALL Failed %s' % ret
        ret = self._post_pkg(pkgpath, noscripts, not_pre_post_script)
        if ret != 0:
            return 'POST_PKG Failed %s' % ret
        return 0
    
if __name__ == '__main__':
    inst_h = InstallRpm()
    pkglist = [(False, '/home/netsec/work/dist/rpm_core/glibc-2.15-32mgc30.i686.rpm', True, True),
               (False, '/home/netsec/work/dist/rpm_core/bash-4.2.29-2mgc30.i686.rpm', True, False),
               (False, '/home/netsec/work/dist/rpm_core/libgcc-4.6.2-2mgc30.1.i686.rpm', True, True),
               (True, '/home/netsec/work/dist/rpm_core/filesystem-3-3mgc30.i686.rpm', True, False),
               ]
    for pkg in pkglist:
        if pkg[0]:
            ret = inst_h.install(*pkg[1:])
            if ret != 0:
                print 'install failed pkg %s' % str(pkg)
            else:
                print 'install success pkg %s' % str(pkg)
                
                
        
    