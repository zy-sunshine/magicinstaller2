# -*- python -*-
# Copyright (C) 2007, MagicLinux.
# Author:  Yang Zhang <zy.netsec@gmail.com>
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
import stat
import sys, glob
from SCons.Action import ActionFactory
from xml.dom.minidom import parse
import PkgMaker

def line_split(lines):
    result = []
    for line in lines.split('\n'):
        line = line.strip()
        if line and line[0] != '#':
            result.append(line)
    return result

def get_node_value(node, name):
    value = ''
    for subnode in node.childNodes:
        if subnode.nodeType == subnode.ELEMENT_NODE \
           and subnode.tagName == name:
            value = ''.join([t.data for t in subnode.childNodes \
                             if t.nodeType == t.TEXT_NODE])
    return line_split(value)

class PkgConfigManager(PkgMaker.BaseMaker):
    def __init__(self, pkgnlist, source_prefix):
        self.source_prefix = source_prefix
        self.source_list = source_list = []
        self.build_cmds = cmds = []
        source_list.extend([ '%s.xml' % a for a in pkgnlist ])
        for pkgcf in source_list:
            self.parseConfig(pkgcf)

    def parseConfig(self, pkgcf):
        try:
            rootdoc = parse(pkgcf)
        except:
            print 'Parser mod %s.xml failed!' % mod
            raise

        # init
        self.inst_list = inst_list = []
        self.pre_list = pre_list = []
        self.post_list = post_list = []
        self.pkg_list = pkg_list = []

        for pkgnode in rootdoc.getElementsByTagName('package'):
            pkgfiles_orig = get_node_value(pkgnode, 'files')
            if pkgfiles_orig:
                pkgfiles = []
                #pkgfiles = self.path_prefix('$source_list_pkg', pkgfiles_orig)
                for pkgfile in pkgfiles_orig:
                    pkg_path = self.search_file(pkgfile, self.source_prefix)
                    if pkg_path:
                        pkgfiles.append(pkg_path)
                    else:
                        print "Can not find the package %s" % pkgfile
                        sys.exit(1)

                pkg_list.extend(pkgfiles)
                # extract
                cmds.extend(self.get_extract_cmd(pkgfiles, '$build_prefix'))
            inst_list.extend(get_node_value(pkgnode, 'install'))
            pre_list.extend(get_node_value(pkgnode, 'pre_action'))
            post_list.extend(get_node_value(pkgnode, 'post_action'))

        # pre_action
        cmds.extend(pre_list)
        # install
        for f in inst_list:
            if f[0] == '+':             # mkdir only
                f = f[1:]
                cmds.extend(['mkdir -p $ROOT/%s' % f])

            elif f[0] == '@':           # recursive
                f = f[1:]
                cmds.extend(['mkdir -p $ROOT/%s' % os.path.dirname(f),
                             'cp -a $BUILD/%s $ROOT/%s/' % (f, os.path.dirname(f))])
            else:
                cmds.extend(['mkdir -p $ROOT/%s' % os.path.dirname(f),
                             'cp -dp $BUILD/%s $ROOT/%s/' % (f, os.path.dirname(f))])
        # post_action
        cmds.extend(post_list)

    def search_file(self, filename, pathes):
        for p in pathes:
            f = os.path.join(p, filename)
            #f = self.env.subst(f)
            files = glob.glob(f)
            if files and os.access(files[0], os.R_OK):
                return files[0]


if __name__ == '__main__':
    pkgnlst = ['filesystem',
                'glibc',
                'syslib',
                'busybox',
                'bash',
                'python',
                'xorg',
                'gtk2',
                'parted',
                #'rhpl',
                'rpm',
                #'debug',
                #'mkfs',
                #'udev',
                #'kudzu',
                #'pyudev',
                #'grub',
                #'trace',
                #'post_scripts',
                ]
    source_prefix = sys.argv[1:]
    pkgManager = PkgConfigManager(pkgnlst, source_prefix)
    print pkgManager.pkg_list

