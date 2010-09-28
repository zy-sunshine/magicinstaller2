#!/usr/bin/python
# Copyright (C) 2010, zy_sunshine.
# Author:  zy_sunshine <zy.netsec@gmail.com>
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


import glob
import os
import os.path
import stat
import string
import sys
import types

from getopt import getopt

import rpm

# Usage:
#    TarPkgInfor.py [-o outputfn] [-l logfn] dirs....

try:
   import pkgpublic
except ImportError:
   sys.path.insert(0, 'scripts')
   import pkgpublic

rpmfn_map = {}

provide_map = {}

# require file --> rpm map
file_requires_map = {}

# rpm's name version release map
rpm_n_v_r_map = {}

def print_rpmfn_map():
   result = '{\n'
   for k in rpmfn_map.keys():
      result = result + "\t'%s': [ %dL,\n" % \
               (k, rpmfn_map[k][pkgpublic.totalsz])
      result = result + "\t\t'%s',\n" % rpmfn_map[k][pkgpublic.path]
      result = result + "\t\t%s," % str(rpmfn_map[k][pkgpublic.group])
      deplist = rpmfn_map[k][pkgpublic.deps]
      if deplist == []:
         result = result + ' [], '
      else:
         for i in range(len(deplist)):
            if i == 0:
               result = result + '\n\t\t['
            else:
               result = result + '\t\t '
            dep = deplist[i]
            if type(dep) == types.StringType:
               result = result + "'%s'" % dep
            else:
               result = result + '%s' % str(dep)
            if i != len(deplist) - 1:
               result = result + ',\n'
            else:
               result = result + '],'
      pathes = rpmfn_map[k][pkgpublic.pathes]
      if pathes == []:
         result = result + ' []]'
      else:
         for i in range(len(pathes)):
            if i == 0:
               result = result + '\n\t\t['
            else:
               result = result + '\t\t '
            result = result + '%s' % str(pathes[i])
            if i != len(pathes) - 1:
               result = result + ',\n'
            else:
               result = result + ']]'
      if k != rpmfn_map.keys()[-1]:
         result = result + ',\n'
   result = result + '}\n'
   return result

optlist, args = getopt(sys.argv[1:], 'o:l:')
outfd = 1
logfd = 2
for (optname, optval) in optlist:
   if optname == '-o':
      if outfd > 2:
         os.close(outfd)
      try:
         outfd = os.open(optval, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
      except OSError:
         outfd = 1
   elif optname == '-l':
      if logfd > 2:
         os.close(logfd)
      try:
         logfd = os.open(optval, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0644)
      except OSError:
         logfd = 2
         
def get_tar_info_from_name(tarpkg):
    dot1 = -1
    dot2 = -1
    tartype = ''
    arch = ''
    pkgname = ''
    try:
        dot1 = tarpkg.rfind('.tar.')
    except:
        pass
    try:
        dot2 = tarpkg.rfind('.', 0, dot1)
    except:
        pass
    # Get tar package type.
    if dot1 != -1:
        tartype = tarpkg[dot1:]
    # Get tar package arch.
    if dot2 != -1 and dot1 != -1 and dot1 > dot2:
        arch = tarpkg[dot2+1:dot1]
    get_arch_failed = False
    if not pkgpublic.arch_map.has_key(arch):
        arch = 'noarch'
        get_arch_failed = True
    # Get package name.
    if dot2 != -1 and not get_arch_failed:
        pkgname = tarpkg[0:dot2]
    elif dot1 != -1:
        pkgname = tarpkg[0:dot1]
    else:
        pkgname = tarpkg
        
    return pkgname, arch, tartype
    
for dir in sys.argv[1:]:
   for rpmfnpath in glob.glob('%s/*' % dir):
      os.write(2, 'Reading %s...\n' % rpmfnpath)
      rpmfn = os.path.basename(rpmfnpath)
      if rpmfn_map.has_key(rpmfn):
         os.write(2, "More then one %s encountered.\n" % rpmfn)
         sys.exit(1)
      rpmstat = os.stat(rpmfnpath)
      rpmsize = rpmstat[stat.ST_SIZE]
      pkgname, arch, tartype = get_tar_info_from_name(rpmfn)
      rpmgroup = ['TarPackage', 'System']
      requires = []
      pathes = [(rpmfnpath, arch, rpmsize)]

      rpmfn_map[rpmfn] = [rpmsize, rpmfnpath, rpmgroup, requires, pathes]

title = '#!/usr/bin/python\n\npackages_infor =\\\n'

os.write(outfd, title + print_rpmfn_map())

if outfd > 2:
   os.close(outfd)
if logfd > 2:
   os.close(logfd)
