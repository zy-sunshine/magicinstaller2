#!/usr/bin/python
import os
from mi.utils.miconfig import MiConfig
from mi.utils.common import run_bash
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
        argv = _argv
        try:
            res = run_bash(cmd, argv, root, cwd='/tmp/%s' % os.path.basename(post_scripts_dir))
        except OSError, e:
            res = {}
            res['ret'] = -1
            res['err'] = 'Can not run %s, can not chroot to target system or can not run this script.' % script_rel
            res['out'] = ''
        cmd0 = 'rm -rf %s/tmp/%s' % (root, os.path.basename(post_scripts_dir))
        logger.d(cmd0)
        os.system(cmd0)
    else:
        cmd = os.path.join(post_scripts_dir, script_rel)
        argv = _argv
        res = run_bash(cmd, argv, cwd=os.path.dirname(cmd))
    
    if res['ret'] != 0:
        return res['ret'], res['err']
    return res['ret'], res['out']

@register.server_handler('long')
def setup_accounts(mia, operid, rootpasswd, acclist):
    # Error detect is not implemented yet.
    password = rootpasswd
    password = password.replace("'", """'"'"'""") # escape ' to '"'"'
    os.system('/usr/sbin/chroot %s /usr/sbin/pwconv' % CF.D.TGTSYS_ROOT)
    #This is ugly, remove it
    #os.system('/bin/sed 1d /tmpfs/tgtsys/etc/passwd > /tmpfs/tgtsys/etc/passwd.bk')
    #os.system('/bin/mv -f /tmpfs/tgtsys/etc/passwd.bk /tmpfs/tgtsys/etc/passwd')
    #os.system('/usr/sbin/chroot /tmpfs/tgtsys  /usr/sbin/useradd -g root -s /bin/bash -d /root -u 0 root')
    os.system("echo '%s' | /usr/sbin/chroot %s /usr/bin/passwd --stdin root" % \
                 (password, CF.D.TGTSYS_ROOT))
    # copy missing skel files to /root
    os.system('/usr/sbin/chroot %s /bin/sh -c ' % CF.D.TGTSYS_ROOT + \
              '"shopt -s dotglob; /bin/cp -a /etc/skel/* /root/"')

    # add normal users
    for (username, password, shell, homedir, realuid) in acclist:
        cmd = '/usr/sbin/chroot %s /usr/sbin/useradd -s %s -d %s %s -G users,fuse,uucp %s' % \
              (CF.D.TGTSYS_ROOT, shell, homedir, '%s', username)
        if realuid == 'Auto':
            cmd = cmd % ''
        else:
            cmd = cmd % ('-u %s' % realuid)
        os.system(cmd)
        password = password.replace("'", """'"'"'""") # escape ' to '"'"'
        os.system("echo '%s' | /usr/sbin/chroot %s /usr/bin/passwd --stdin %s" % \
                  (password, CF.D.TGTSYS_ROOT, username))
    return 0, ''


@register.server_handler('long')
def do_mkinitrd(mia, operid, dummy):
    mia.set_step(operid, 0, -1)
    return run_post_script('geninitrd', [CF.D.DISTKERNELVER, ])

@register.server_handler('long')
def do_genfstab(mia, operid, dummy):
    mia.set_step(operid, 0, -1)
    return run_post_script('genfstab', [CF.D.TGTSYS_ROOT, ], False)
    
@register.server_handler('long')
def setup_grub2(mia, operid, timeout, usepassword, password,
                 lba, options, entrylist, default, instpos, bootdev, mbrdev, windev, winfs):
    mia.set_step(operid, 0, -1)
    return run_post_script('post-grub2', [mbrdev, str(options), str(timeout)])
    
@register.server_handler('long')
def run_post_install(mia, operid, dummy):
    mia.set_step(operid, 0, -1)
    return run_post_script('post-install')

@register.server_handler('long')
def clean_server_env(mia, operid, dummy):
    logger.i('clean_server_env')
    return 0

@register.server_handler('long')
def finish(mia, operid, dummy):
    logger.i('finish install')
    return 0
