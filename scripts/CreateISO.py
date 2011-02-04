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

# Usage:
#   CreateISO.py TARGET_ISO PKG_ARR PKG_DIRS ISO_DIR DIST_NAME DIST_VER SET_NO
#                NEED_CLEAN [BOOT_FILE]
#
#     TARGET_ISO:    The filename of the target iso.
#     PKG_ARR:       The filename of the pkgarr.py or pkgarr.pyc.
#           If PKG_ARR is none we will do nothing with packages.
#     PKG_DIRS:      The ':' separated directory list of packages.
#           If PKG_ARR is none we will also do nothing with it. So it can be
#           none too.
#     ISO_DIR:       The directory name of the target iso.
#     DIST_NAME:     The name of the distribution.
#     DIST_VER:      The version of the distribution.
#     SET_NO:        The no of the target iso.
#     NEED_CLEAN     Whether to clean the packages directory. [clean | notclean]
#           If NEED_CLEAN is clean, this script will clean last packages in
#           PKG_DIRS, notclean will not do this.
#     BOOT_FILE:     The boot image file name.

import os
import os.path
import string
import sys

try:
    import pkgpublic
except ImportError:
    sys.path.insert(0, 'scripts')
    import pkgpublic

def os_system(cmd):
    print '+', cmd
    ret = os.system(cmd)
    if ret != 0:
        os.write(2, '(%s) FAILED with %d!' % (cmd, ret))
        sys.exit(1)

target_iso    = sys.argv[1]
pkg_arr       = sys.argv[2]
pkg_dirs      = sys.argv[3]
iso_dir       = sys.argv[4]
dist_name     = sys.argv[5]
dist_ver      = sys.argv[6]
set_no        = sys.argv[7]
need_clean    = sys.argv[8]

if len(sys.argv) > 9:
    bootload = sys.argv[9]
    bootdir = sys.argv[10]
    if bootload == 'syslinux':
        boot_flags = ' '.join(('-b %s/mbboot' % bootdir,
                               '-c %s/boot.cat' % bootdir,
                               ))
        #boot_flags = string.join(('-b', sys.argv[8],
        #'-c', 'miimages/boot.cat',
        #'-no-emul-boot',
        #'-boot-load-size', '2880'))
    else:
        boot_flags = ' '.join(('-b %s/grub/grldr' % bootdir, #'-b %s/grub/stage2_eltorito' % bootdir,
                               '-c %s/grub/boot.cat' % bootdir,
                               '-no-emul-boot',
                               '-boot-load-size 4',
                               '-boot-info-table',
                               ))
else:
    boot_flags = ''

set_no = int(set_no) - 1

arrangement = None
if pkg_arr != 'none':
    g_map = {}
    l_map = {}
    execfile(pkg_arr, g_map, l_map)
    del(g_map)

    arrangement = l_map['arrangement']
    if set_no >= len(arrangement):
        print '%s is blank.' % target_iso
        sys.exit(0)
else:
    if set_no >= 1:
        print 'Have none pkgarr, so %s is blank.' % target_iso
        sys.exit(0)

if pkg_arr != 'none':
    cd_pkg_dir = os.path.join(iso_dir, dist_name, 'packages')
    os_system('mkdir -p %s' % cd_pkg_dir)

    # Copy packages from package directories into iso_dir.
    rpm_files = []
    for pkgtuple in arrangement[set_no]:
        for pkgpathtuple in pkgtuple[pkgpublic.pathes]:
            rpm_files.append(pkgpathtuple[0])
    rpm_files = list(set(rpm_files))
    
    #  find rsync and use it if possible
    rsync_found = False
    #DISABLE rsync, use ln only now
    # for path in os.environ['PATH'].split(':'):
    #     if os.path.isfile(os.path.join(path, 'rsync')):
    #         rsync_found = True
    #         break
    if not rsync_found:
        if need_clean == 'clean':
            os_system('rm -f %s/*' % cd_pkg_dir)
        for fn in rpm_files:
            os_system('ln -s %s %s' % (os.path.abspath(fn), cd_pkg_dir))
    else:
        cmd = 'rsync --files-from=- --no-relative -v / %s' % cd_pkg_dir
        print '+', cmd
        f = os.popen(cmd, 'w')
        for fn in rpm_files:
            f.write(os.path.abspath(fn) + '\n')
        f.close()

    if need_clean == 'clean':
        # delete old rpms
        basename_list = []
        for fn in rpm_files:
            basename_list.append(os.path.basename(fn))
        for (dirpath, dirnames, filenames) in os.walk(cd_pkg_dir):
            for fn in filenames:
                if fn not in basename_list:
                    os_system('rm -f %s' % os.path.join(dirpath, fn))

os_system('mkisofs -V %s-%s-%s %s -J -T -r -f -o %s %s' % \
          (dist_name, dist_ver, set_no + 1, boot_flags,
           target_iso, iso_dir))
