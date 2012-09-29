import os

def pre_install():
    '''
        all packages install operation previous action.
    '''

def pre_pkg():
    '''
        each package install operation previous action.
    '''

class CBFileObj(file):
    def __init__(self, filepath, data):
        self.mia, self.operid, self.total_size = data
        file.__init__(self, filepath)
    def read(self, size):
        self.mia.set_step(self.operid, self.tell(), self.total_size)
        return file.read(self, size)

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
    
def install_pkg():
    '''
        each package install operation.
    '''
    ret = do_tar_extract_install()
    if ret:
        return ret
    else:
        return 0

def post_pkg():
    '''
        each package install operation post action.
    '''

def post_install():
    '''
        all packages install finish post action.
    '''
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
