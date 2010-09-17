#!/usr/bin/python
# Copyright (C) 2003, Charles Wang.
# Author:  Charles Wang <charles@linux.net.cn>
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANT; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public LIcense for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.

import os

if operation_type == 'short':
    pass
elif operation_type == 'long':
    def setup_accounts(mia, operid, rootpasswd, acclist):
        # Error detect is not implemented yet.
        password = rootpasswd
        password = password.replace("'", """'"'"'""") # escape ' to '"'"'
        os.system('/usr/sbin/chroot %s /usr/sbin/pwconv' % tgtsys_root)
        #This is ugly, remove it
        #os.system('/bin/sed 1d /tmpfs/tgtsys/etc/passwd > /tmpfs/tgtsys/etc/passwd.bk')
        #os.system('/bin/mv -f /tmpfs/tgtsys/etc/passwd.bk /tmpfs/tgtsys/etc/passwd')
        #os.system('/usr/sbin/chroot /tmpfs/tgtsys  /usr/sbin/useradd -g root -s /bin/bash -d /root -u 0 root')
        os.system("echo '%s' | /usr/sbin/chroot %s /usr/bin/passwd --stdin root" % \
                     (password, tgtsys_root))
        # copy missing skel files to /root
        os.system('/usr/sbin/chroot %s /bin/sh -c ' % tgtsys_root + \
                  '"shopt -s dotglob; /bin/cp -a /etc/skel/* /root/"')

        # add normal users
        for (username, password, shell, homedir, realuid) in acclist:
            cmd = '/usr/sbin/chroot %s /usr/sbin/useradd -s %s -d %s %s -G users,fuse,uucp %s' % \
                  (tgtsys_root, shell, homedir, '%s', username)
            if realuid == 'Auto':
                cmd = cmd % ''
            else:
                cmd = cmd % ('-u %s' % realuid)
            os.system(cmd)
            password = password.replace("'", """'"'"'""") # escape ' to '"'"'
            os.system("echo '%s' | /usr/sbin/chroot %s /usr/bin/passwd --stdin %s" % \
                      (password, tgtsys_root, username))
        return 0

    def run_post_install(mia, operid, dummy):
        script = '/root/post_install.sh'
        if os.access(script, os.X_OK):
            dolog('Run %s\n' % script)
            sys_root_dir = os.path.join(tgtsys_root, 'root')
            if not os.path.isdir(sys_root_dir):
                os.makedirs(sys_root_dir)
            os.system('cp %s %s' % (script, os.path.join(tgtsys_root, 'root')))
            os.system('/usr/sbin/chroot %s %s 1>&2' % (tgtsys_root, script))
            if os.path.exists(os.path.join(tgtsys_root, script[1:])):
                os.remove(os.path.join(tgtsys_root, script[1:]))
        return 0
