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
import string

if operation_type == 'short':
    def get_arch():
        (sysname, nodename, release, version, machine) = os.uname()
        if machine == 'i686':
            f = file('/proc/cpuinfo')
            cimap = {}
            l = f.readline()
            while l:
                a = string.split(l, ':')
                if len(a) == 2:
                    (key, val) = string.split(l, ':')
                    key = string.strip(key)
                    val = string.strip(val)
                    cimap[key] = val
                l = f.readline()
            f.close()
            if cimap.has_key('model name') and \
               string.find(string.lower(cimap['model name']), 'athlon') >= 0:
                machine = 'athlon'
        return machine

elif operation_type == 'long':
    pass
