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

import os.path

#import kudzu
import getdev

if operation_type == 'short':
    def config_network_short(hostname):
        hosts = os.path.join(tgtsys_root, 'etc/hosts')

        outhn = hostname
        if hostname != '':
            outhn = hostname + ' '
        else:
            outhn = 'localhost'
        os.system('echo -e "127.0.0.1\t%slocalhost.localdomain localhost" > %s' % (outhn, hosts))

        networkdir = os.path.join(tgtsys_root, 'etc/sysconfig')
        network = os.path.join(networkdir, 'network')
        os.system('mkdir -p %s' % networkdir)
        os.system('echo NETWORKING=yes > %s' % network)

        if hostname == '':
            outhn = 'localhost'
        else:
            outhn = hostname
        os.system('echo HOSTNAME=%s >> %s' % (outhn, network))

        HOSTNAME = os.path.join(tgtsys_root, 'etc/HOSTNAME')
        os.system('echo %s > %s' % (outhn, HOSTNAME))

        resolv_conf = os.path.join(tgtsys_root, 'etc/resolv.conf')
        os.system('echo /dev/null > %s' % resolv_conf)
        os.system('chmod 644 %s' % resolv_conf)

        return  0

elif operation_type == 'long':
    pass
