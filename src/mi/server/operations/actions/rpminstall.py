import os
from mi.server.utils import logger, CF
from mi.utils.miregister import MiRegister
register = MiRegister()

USE_TS = False
inst_h = None

@register.server_handler('long', 'rpm_pre_install')
def pre_install(mia, operid):
    '''
        all packages install operation previous action.
    '''
    global inst_h
    if USE_TS:
        # Use rpm-python module to install rpm pkg, but at this version it is very slowly.
        from mi.server.utils.rpm.pyrpm_install import InstallRpm
        inst_h = InstallRpm(CF.D.TGTSYS_ROOT)
        inst_h.install_pre()
    else:
        # Because I can not use rpm-python module to install quickly.
        # So use the bash mode to install the pkg, it is very fast.
        # If you can use rpm-python module install pkg quickly, you can remove it.
        from mi.server.utils.rpm.rpm_cmd_install import InstallRpm
        inst_h = InstallRpm(CF.D.TGTSYS_ROOT)
        inst_h.install_pre()

@register.server_handler('long', 'rpm_pre_pkg')
def pre_pkg(mia, operid):
    '''
        each package install operation previous action.
    '''
    mia.set_step(operid, 0, 1)
    
@register.server_handler('long', 'rpm_install_pkg')
def install_pkg(mia, operid, pkgname, firstpkg):
    '''
        each package install operation.
        firstpkg?? haha actually it is used to get other packages dirname, because these packages are in same dir.
    '''
    
    dev_hd = CF.S.pkg_res_dev_hd
    dev_iso = CF.S.pkg_res_dev_iso
    if not (dev_hd or dev_iso):
        return _('Can not get the mounted resource device (iso or harddisk both None), ERROR!!!')
    
    pkgpath = os.path.join(os.path.dirname(firstpkg), pkgname)
    pkgpath = dev_iso and dev_iso.get_file_path(pkgpath) or dev_hd.get_file_path(pkgpath)
    #dolog('pkg_install(%s, %s)\n' % (pkgname, str(pkgpath)))

    # Decide using which mode to install.
    class Progress_CB():
        def __init__(self, mia, operid):
            self.mia = mia
            self.operid = operid
            
        def set_step(self, step, total):
            self.mia.set_step(self.operid, step, total)
            
    ret = 'Nothing'
    if USE_TS:
        # Use rpm-python module to install rpm pkg, but at this version it is very slowly.
        ret = inst_h.install(pkgpath, , Progress_CB(mia, operid))
    else:
        # Because I can not use rpm-python module to install quickly.
        # So use the bash mode to install the pkg, it is very fast.
        # If you can use rpm-python module install pkg quickly, you can remove it.
        ret = inst_h.install(pkgpath, Progress_CB(mia, operid))

    return ret

@register.server_handler('long', 'rpm_post_pkg')
def post_pkg(mia, operid):
    '''
        each package install operation post action.
    '''
    mia.set_step(operid, 1, 1)
    
@register.server_handler('long', 'rpm_post_install')
def post_install(mia, operid):
    '''
        all packages install finish post action.
    '''
    inst_h.install_post()
