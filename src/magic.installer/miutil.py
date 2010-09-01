#!/usr/bin/python
# Copyright (C) 2006, Levin Du.
# Author:  Levin Du <zsdjw@21cn.com>
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
from mipublic import *
import os.path
import sys
import isys

class AttrDict(dict):
    """A dict class, holding the dict. Two extra method to get dict
    value, e.g.:
    attrs = attrs_dict(cat)
    attrs.tips
    attrs('tips')"""
    def __init__(self, d={}):
        self.d = d
    def __call__(self, arg):
        return self.get(arg, None)
    def __getattr__(self, attr):
        return self.get(attr, None)

class NamedTuple(tuple):
    """Access a tuple by attribute name. e.g.:
    class AutoPartTuple(NamedTuple):
        attr_oder = ['mountpoint', 'size', 'filesystem']

    part = ('/', '32G', 'ext2')
    part = AutoPartTuple(part)
    print part.mountpoint,  part.size, part.filesystem
    """
    attr_order = []
    def __init__(self, seq):
        tuple.__init__(self, seq)

    def __getattr__(self, attr):
        idx = self.attr_order.index(attr)
        return self[idx]

def mount_dev(devfn, fstype, readonly):
    mntdir = os.path.join('/tmpfs/mnt', os.path.basename(devfn))
    dolog("mount_dev: Device = %s Mount = %s Fstype = %s\n" % \
          (devfn, mntdir, fstype))
    if not os.path.isdir(mntdir):
        os.makedirs(mntdir)
    try:
        isys.mount(fstype, devfn, mntdir, readonly, 0)
    except SystemError, errmsg:
        dolog("mount_dev: mount failed: %s\n" % str(errmsg))
        return None
    else:
        return mntdir

def umount_dev(mntdir):
    try:
        isys.umount(mntdir)
    except SystemError, errmsg:
        dolog("umount_dev: umount failed: %s\n" % str(errmsg))
        return False
    else:
        return True

def search_file(filename, pathes,
                prefix = '', postfix = '',
                exit_if_not_found = True):
    for p in pathes:
        f = os.path.join(prefix, p, postfix, filename)
        if os.access(f, os.R_OK):
            return f
    if exit_if_not_found:
        os.write(sys.stderr, ("Can't find %s in " % filename) + \
                 str(pathes))
        sys.exit(1)
    return None

def convert_str_size(size):
    "Convert SIZE of 1K, 2M, 3G to bytes"
    if not size:
        return 0
    k = 1
    try:
        size = int(float(size))
    except ValueError:
        if size[-1] in ('k', 'K'):
            k = 1024
        elif size[-1] in ('m', 'M'):
            k = 1024 * 1024
        elif size[-1] in ('g', 'G'):
            k = 1024 * 1024 * 1024
        try:
            size = int(float(size[:-1]))
        except ValueError:
            return None
    return size * k

logf = None

def openlog(filename):
    global logf, dolog
    if dolog:
    	try:
            logf = file(filename, 'w')
    	except:
            print 'Open log file %s failed.\n' % filename
            logf = None

def dolog(str):
    global logf, dolog
    if dolog:
        if logf:
            logf.write(str)
            logf.flush()
    	print str,

def closelog():
    global logf, dolog
    if dolog:
    	if logf:
            logf.close()

