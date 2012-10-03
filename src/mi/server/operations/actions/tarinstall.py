import os
from mi.utils.miregister import MiRegister
register = MiRegister()

@register.server_handler('long', 'tar_pre_install')
def pre_install(mia, operid):
    '''
        all packages install operation previous action.
    '''
@register.server_handler('long', 'tar_pre_pkg')
def pre_pkg(mia, operid):
    '''
        each package install operation previous action.
    '''
    
@register.server_handler('long', 'tar_install_pkg')
def install_pkg(mia, operid):
    '''
        each package install operation.
    '''
    ret = do_tar_extract_install()
    return ret
    
@register.server_handler('long', 'tar_post_pkg')
def post_pkg(mia, operid):
    '''
        each package install operation post action.
    '''
    
@register.server_handler('long', 'tar_post_install')
def post_install(mia, operid):
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
