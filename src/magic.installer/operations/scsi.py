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

if operation_type == 'short':
    def get_all_scsi_modules():
        def scan_scsi_module_dir(the_list, dirname, name):
            mod_ext = os.uname()[2][:3] > '2.4' and '.ko' or '.o'
            for bn in name:
                filename = os.path.join(dirname, bn)
                if os.path.isfile(filename) and os.path.splitext(bn)[1] == mod_ext:
                    the_list.append(os.path.splitext(bn)[0])

        scsi_module_list = []
        os.path.walk(os.path.join('/lib/modules', kernelver, 'kernel/drivers/scsi'),
                     scan_scsi_module_dir, scsi_module_list)
        return  scsi_module_list

    def get_all_loaded_modules():
        loaded_module_list = []
        mods = file('/proc/modules')
        l = mods.readline()
        while l:
            loaded_module_list.append(string.split(l)[0])
            l = mods.readline()
        mods.close()
        return  loaded_module_list

elif operation_type == 'long':
    def do_modprobe(mia, operid, module):
        def get_all_loaded_modules():
            loaded_module_list = []
            mods = file('/proc/modules')
            l = mods.readline()
            while l:
                loaded_module_list.append(string.split(l)[0])
                l = mods.readline()
            mods.close()
            return  loaded_module_list

        modlist = get_all_loaded_modules()
        if not 'sd_mod' in modlist:
            os.system('/sbin/modprobe sd_mod 2>/dev/null')
        if not module in modlist:
            os.system('/sbin/modprobe %s' % module)

        modlist = get_all_loaded_modules()
        return (module in modlist) #('sd_mod' in modlist) and (module in modlist)

    def scsi_modprobe_conf(mia, operid, scsi_module_list):
        global  tgtsys_root

        mconf = file(os.path.join(tgtsys_root, 'etc/modules.conf'), 'a')
        mpconf = file(os.path.join(tgtsys_root, 'etc/modprobe.conf'), 'a')
        for module in string.split(scsi_module_list, '/'):
            mconf.write('alias scsi_hostadapter %s\n' % module)
            mpconf.write('alias scsi_hostadapter %s\n' % module)
        mpconf.close()
        mconf.close()
        return  0
