#!/usr/bin/python
import os
from miutils.miconfig import MiConfig
CONF = MiConfig.get_instance()
CONF_TGTSYS_ROOT = CONF.LOAD.CONF_TGTSYS_ROOT
from miutils.miregister import MiRegister
register = MiRegister()

from miserver.utils import Logger
Log = Logger.get_instance(__name__)
dolog = Log.i

@register.server_handler('long')
def setup_accounts(mia, operid, rootpasswd, acclist):
    # Error detect is not implemented yet.
    password = rootpasswd
    password = password.replace("'", """'"'"'""") # escape ' to '"'"'
    os.system('/usr/sbin/chroot %s /usr/sbin/pwconv' % CONF_TGTSYS_ROOT)
    #This is ugly, remove it
    #os.system('/bin/sed 1d /tmpfs/tgtsys/etc/passwd > /tmpfs/tgtsys/etc/passwd.bk')
    #os.system('/bin/mv -f /tmpfs/tgtsys/etc/passwd.bk /tmpfs/tgtsys/etc/passwd')
    #os.system('/usr/sbin/chroot /tmpfs/tgtsys  /usr/sbin/useradd -g root -s /bin/bash -d /root -u 0 root')
    os.system("echo '%s' | /usr/sbin/chroot %s /usr/bin/passwd --stdin root" % \
                 (password, CONF_TGTSYS_ROOT))
    # copy missing skel files to /root
    os.system('/usr/sbin/chroot %s /bin/sh -c ' % CONF_TGTSYS_ROOT + \
              '"shopt -s dotglob; /bin/cp -a /etc/skel/* /root/"')

    # add normal users
    for (username, password, shell, homedir, realuid) in acclist:
        cmd = '/usr/sbin/chroot %s /usr/sbin/useradd -s %s -d %s %s -G users,fuse,uucp %s' % \
              (CONF_TGTSYS_ROOT, shell, homedir, '%s', username)
        if realuid == 'Auto':
            cmd = cmd % ''
        else:
            cmd = cmd % ('-u %s' % realuid)
        os.system(cmd)
        password = password.replace("'", """'"'"'""") # escape ' to '"'"'
        os.system("echo '%s' | /usr/sbin/chroot %s /usr/bin/passwd --stdin %s" % \
                  (password, CONF_TGTSYS_ROOT, username))
    return 0

@register.server_handler('long')
def run_post_install(mia, operid, dummy):
    script = '/root/post_install.sh'
    if os.access(script, os.X_OK):
        dolog('Run %s\n' % script)
        sys_root_dir = os.path.join(CONF_TGTSYS_ROOT, 'root')
        if not os.path.isdir(sys_root_dir):
            os.makedirs(sys_root_dir)
        os.system('cp %s %s' % (script, os.path.join(CONF_TGTSYS_ROOT, 'root')))
        os.system('/usr/sbin/chroot %s %s 1>&2' % (CONF_TGTSYS_ROOT, script))
        if os.path.exists(os.path.join(CONF_TGTSYS_ROOT, script[1:])):
            os.remove(os.path.join(CONF_TGTSYS_ROOT, script[1:]))
    return 0
