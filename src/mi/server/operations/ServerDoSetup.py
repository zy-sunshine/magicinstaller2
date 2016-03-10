#!/usr/bin/python
import os
from mi.utils.miconfig import MiConfig
from mi.utils.common import run_bash
import sys
CF = MiConfig.get_instance()
from mi.utils.miregister import MiRegister
register = MiRegister()

from mi.server.utils import logger
dolog = logger.info

def run_post_script(script_rel, _argv=[], f_chroot=True):
    logger.i('Run post_script %s %s' % (script_rel, str(_argv)))
    post_scripts_dir = CF.D.POST_SCRIPTS_DIR
    script = os.path.join(post_scripts_dir, script_rel)
    if not os.path.exists(script):
        msg = _('Can not find the script %s' % script)
        logger.e(msg)
        return -1, msg
    
    root = CF.D.TGTSYS_ROOT
    if f_chroot:
        if not os.path.exists('%s/tmp' % root):
            os.makedirs('%s/tmp' % root)
        cmd0 = 'cp -pr %s %s/tmp/' % (post_scripts_dir, root)
        logger.d(cmd0)
        os.system(cmd0)
        cmd = '/tmp/%s/%s' % (os.path.basename(post_scripts_dir), script_rel)
        cmd0 = 'chmod 777 %s%s' % (root, cmd)
        logger.d(cmd0)
        os.system(cmd0)
        argv = _argv
        _environ = dict(os.environ)
        _environ['LANG'] = 'en_US.UTF-8'
        try:
            res = run_bash(cmd, argv, root, env=_environ, cwd='/tmp/%s' % os.path.basename(post_scripts_dir))
        except OSError, e:
            res = {}
            res['ret'] = -1
            res['err'] = ['Can not run %s, can not chroot to target system or can not run this script.' % script_rel]
            res['out'] = ['']
            logger.e(res['err'], exc_info = sys.exc_info())
        cmd0 = 'rm -rf %s/tmp/%s' % (root, os.path.basename(post_scripts_dir))
        logger.d(cmd0)
        os.system(cmd0)
    else:
        cmd = os.path.join(post_scripts_dir, script_rel)
        argv = _argv
        res = run_bash(cmd, argv, cwd=os.path.dirname(cmd))
    
    if res['ret'] != 0:
        return res['ret'], ' '.join(res['err'])
    return res['ret'], ' '.join(res['out'])

@register.server_handler('long')
def setup_accounts(mia, operid, rootpasswd, acclist):
    mia.set_step(operid, 0, -1)

    argv = [rootpasswd, ]
    for (username, password, shell, homedir, realuid) in acclist:
        argv.extend([username, password, shell, homedir, realuid])
    ret, msg = run_post_script('setup-accounts', argv)
    if ret == 0:
        return 0, ''
    else:
        return ret, str(msg)

@register.server_handler('long')
def do_mkinitrd(mia, operid, dummy):
    mia.set_step(operid, 0, -1)
    return run_post_script('geninitrd', [CF.D.DISTKERNELVER, ])

@register.server_handler('long')
def do_genfstab(mia, operid, dummy):
    mia.set_step(operid, 0, -1)
    #return run_post_script('genfstab', [CF.D.TGTSYS_ROOT, ], False)
    return run_post_script('genfstab')
    
@register.server_handler('long')
def setup_grub2(mia, operid, timeout, usepassword, password,
                 lba, options, entrylist, default, instpos, bootdev, mbrdev, windev, winfs):
    mia.set_step(operid, 0, -1)
    return run_post_script('post-grub2', [mbrdev, str(options), str(timeout)])

@register.server_handler('long')    
def setup_none(mia, operid, *args):
    '''
    Do not install bootloader on target system.
    '''
    mia.set_step(operid, 0, -1)
    return 0

@register.server_handler('long')
def run_post_install(mia, operid, dummy):
    mia.set_step(operid, 0, -1)
    return run_post_script('post-install')

@register.server_handler('long')
def backup_mi_logfiles(mia, operid, dummy):
    logdir = os.path.join(CF.D.TGTSYS_ROOT, 'var/log/MagicInstaller')
    os.system('mkdir -p %s' % logdir)
    os.system('cp /tmpfs/var/log/* %s' % logdir)
    os.system('cp /tmpfs/grub.* %s' % logdir)
    return 0

@register.server_handler('long')
def clean_server_env(mia, operid, dummy):
    logger.i('clean_server_env')
    return 0

@register.server_handler('long')
def finish(mia, operid, dummy):
    logger.i('finish install')
    return 0
