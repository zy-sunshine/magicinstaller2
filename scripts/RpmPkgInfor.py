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
#    RpmPkgInfor.py [-o outputfn] [-l logfn] dirs....

try:
   import pkgpublic
except ImportError:
   sys.path.insert(0, 'scripts')
   import pkgpublic

#import rpmshow

basement_arches = {'i386' : 'y','i586' : 'y', 'i686' : 'y', 'noarch' : 'y'}

instpath = 'root'

# Same as flag in PkgArrage.py
use_script_in_dep = False
script_in_dep = {}

ts = rpm.TransactionSet(instpath)
ts.setVSFlags(rpm.RPMVSF_NODSA | rpm.RPMVSF_NORSA | rpm.RPMVSF_NODSAHEADER)

omit_require = {'rpmlib(VersionedDependencies)' : 'y',
                'rpmlib(PayloadFilesHavePrefix)' : 'y',
}

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

for dir in sys.argv[1:]:
   for rpmfnpath in glob.glob('%s/*.rpm' % dir):
      os.write(2, 'Reading %s...\n' % rpmfnpath)
      rpmfn = os.path.basename(rpmfnpath)
      if rpmfn_map.has_key(rpmfn):
         os.write(2, "More then one %s encountered.\n" % rpmfn)
         sys.exit(1)
      rpmstat = os.stat(rpmfnpath)
      rpmsize = rpmstat[stat.ST_SIZE]
      rpmfd = os.open(rpmfnpath, os.O_RDONLY)
      hdr = ts.hdrFromFdno(rpmfd)
      os.close(rpmfd)
      #rpmshow.addHdr(hdr)
      # Fill rpm_n_v_r_map.
      rpmname    = hdr[rpm.RPMTAG_NAME]
      rpmversion = hdr[rpm.RPMTAG_VERSION]
      rpmrelease = hdr[rpm.RPMTAG_RELEASE]
      rpmarch    = hdr[rpm.RPMTAG_ARCH]
      n_v_r_key = '%s-%s-%s' % (rpmname, rpmversion, rpmrelease)
      if rpm_n_v_r_map.has_key(n_v_r_key):
         rpm_n_v_r_map[n_v_r_key].append((rpmfnpath, rpmarch, rpmsize))
      else:
         rpm_n_v_r_map[n_v_r_key] = [(rpmfnpath, rpmarch, rpmsize)]
      if not basement_arches.has_key(rpmarch):
         continue
      rpmgroup   = string.split(hdr[rpm.RPMTAG_GROUP], '/')
      # Fill provides and record requires.
      provide_name = hdr[rpm.RPMTAG_PROVIDENAME]
      provide_version = hdr[rpm.RPMTAG_PROVIDEVERSION]
      provide_flags = hdr[rpm.RPMTAG_PROVIDEFLAGS]
      n_provides = len(provide_name)
      if n_provides == 1 and type(provide_flags) != types.ListType:
         provide_flags = [provide_flags]
      for i in range(n_provides):
         provide_tuple = (rpmfn,
                          provide_version[i],
                          provide_flags[i])
         if provide_map.has_key(provide_name[i]):
            provide_map[provide_name[i]].append(provide_tuple)
         else:
            provide_map[provide_name[i]] = [provide_tuple]
      requires = []
      require_name = hdr[rpm.RPMTAG_REQUIRENAME]
      require_version = hdr[rpm.RPMTAG_REQUIREVERSION]
      require_flags = hdr[rpm.RPMTAG_REQUIREFLAGS]
      n_requires = len(require_name)
      if n_requires == 1 and type(require_flags) != types.ListType:
         require_flags = [require_flags]
      for i in range(n_requires):
         requires_tuple = (require_name[i],
                           require_version[i],
                           require_flags[i])
         if not omit_require.has_key(require_name[i]) \
                and not require_name[i].startswith('rpmlib('):
            requires.append(requires_tuple)
         if string.find(require_name[i], '/') >= 0:
            file_requires_map[require_name[i]] = 'y'
      # Place n_v_r_key in pkgpublic.pathes position temporary.
      rpmfn_map[rpmfn] = [0, rpmfnpath, rpmgroup, requires, n_v_r_key]

# Search all keys in file_requires_map.
for rpmfn in rpmfn_map.keys():
   os.write(2, 'Reread %s...\n' % rpmfn_map[rpmfn][pkgpublic.path])
   rpmfd = os.open(rpmfn_map[rpmfn][pkgpublic.path], os.O_RDONLY)
   hdr = ts.hdrFromFdno(rpmfd)
   os.close(rpmfd)
   for f in hdr[rpm.RPMTAG_FILENAMES]:
      if file_requires_map.has_key(f):
         if file_requires_map[f] == 'y':
            file_requires_map[f] = rpmfn
         else:
            os.write(logfd,
                     "Warning: '%s' provide '%s', but it is provided by '%s' already. Use '%s'\n" % \
                  (rpmfn, f, file_requires_map[f], file_requires_map[f]))

def get_dep_from_provide_map(require):
    reqname = require[0]
    if provide_map.has_key(reqname):
        prov_rpm = provide_map[reqname][0][0]
        if len(provide_map[reqname]) > 1:
            diff_prov = None
            for prov in provide_map[reqname]:
                if prov[0] != prov_rpm:
                    diff_prov = 1
                    break
            if diff_prov:
                os.write(logfd, 'Warning: Multiple provide(Use %s): \'%s\'.\n' % (prov_rpm, reqname))
                for prov in provide_map[reqname]:
                    os.write(logfd, '\t%s\n' % str(prov))
        return (prov_rpm, require[1], require[2])
    else:
        return None
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
#--------------------------------------------
#  I want to implement the pkg satisfaction compare. but I find it is difficult
#  to judge the version by flags, and flags will change in future rpm version.
#  So I give up this function.
#  There have another way to get the dependency list: 
#        use the ts.addInstall() ts.order() ts.check() function 
#  But I only check the pre script's satisfaction, in order to ensure the rpm install 
#  progress successfully.
#-------------------------------------------

def print_script_in_dep():
    str = 'script_in_dep = \\\n{'
    for key in script_in_dep.keys():
        str += "\n\t'%s': [[" % key
        for pkg in script_in_dep[key]:
            str += "\n\t\t'%s'," % pkg
        str += "]],"
    str += "\n\t}"
    return str

def get_pre_providepkg(require, rpmfn):
    reqname = require[0]
    if file_requires_map.has_key(reqname):
        if file_requires_map[reqname] != 'y':
            return file_requires_map[reqname]      # the pkg which provide the file
        else:
            os.write(logfd, "Error: Unresolvable pre script require for '%s': '%s'.\n" % \
                         (rpmfn, reqname))
            return None
    else:
        req_tuple = get_dep_from_provide_map(require)
        if req_tuple:
            return req_tuple[0]
        else:
            return None

def fill_script_in_dep():
    global script_in_dep
    for rpmfn in rpmfn_map.keys():
        for require in rpmfn_map[rpmfn][pkgpublic.deps]:
            flag = require[2]
            reqname = require[0]
            if flag & rpm.RPMSENSE_SCRIPT_PRE or flag & rpm.RPMSENSE_SCRIPT_POST:
                # Require for pre and post script
                providepkg = get_pre_providepkg(require, rpmfn)
                if providepkg:
                    if script_in_dep.has_key(rpmfn):
                        script_in_dep[rpmfn].append(providepkg)
                    else:
                        script_in_dep[rpmfn] = [providepkg]
                else:
                     os.write(logfd, "Error: Unresolvable require for '%s': '%s'.\n" % \
                            (rpmfn, reqname))
    for rpmfn in script_in_dep.keys():
        script_in_dep[rpmfn] = list(set(script_in_dep[rpmfn]))
        # Compress newrequies. Some information is lost here.
        reqmap = {}
        for req in script_in_dep[rpmfn]:
            if req != rpmfn:
                # Omit the self-dependency.
                reqmap[req] = 'y'
        script_in_dep[rpmfn] = reqmap.keys()

if use_script_in_dep:
    fill_script_in_dep()

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

#for f in file_requires_map.keys():
#   if file_requires_map[f] == 'y':
#      os.write(logfd, "Error: Unresolvable require(file): '%s'\n" % f)

# Convert all require/provide to rpm package name.
for rpmfn in rpmfn_map.keys():
   newrequires = []
   for require in rpmfn_map[rpmfn][pkgpublic.deps]:
      reqname = require[0]
      #if 0 <= string.find(reqname, '(') and \
      #       string.find(reqname, '(') <= string.find(reqname, ')'):
      #   continue  # Omit the xxx(xxx) dependency.

      # Fill the FILE require relations.
      if string.find(reqname, '/') >= 0:
         # Deal with file dependency latter.
         if file_requires_map[reqname] != 'y':
            newrequires.append((file_requires_map[reqname], require[1], require[2]))
         else:
            os.write(logfd, "Error: Unresolvable require for '%s': '%s'.\n" % \
                     (rpmfn, reqname))
      # Other ralations ,we can search from provide_map.
      # Additionally, we must check the version(use the flag).
      else:
         dep_tuple = get_dep_from_provide_map(require)
         if dep_tuple:
            newrequires.append(dep_tuple)
         else:
            os.write(logfd, "Error: Unresolvable require for '%s': '%s'.\n" % \
                    (rpmfn, reqname))
   # Compress newrequies. Some information is lost here (lost the
   # self-contained information), but if the specified
   # rpm package is self-contained, things will be ok.
   reqmap = {}
   for requires in newrequires:
      if requires[0] != rpmfn:
         # Omit the self-dependency.
         reqmap[requires[0]] = 'y'
   rpmfn_map[rpmfn][pkgpublic.deps] = reqmap.keys()
# Fill pkgpublic.totalsz and pkgpublic.pathes.
for rpmfn in rpmfn_map.keys():
   n_v_r_key = rpmfn_map[rpmfn][pkgpublic.pathes]
   rpmfn_map[rpmfn][pkgpublic.pathes] = rpm_n_v_r_map[n_v_r_key]
   for (rpmfnpath, rpmarch, rpmsize) in rpm_n_v_r_map[n_v_r_key]:
      rpmfn_map[rpmfn][pkgpublic.totalsz] += rpmsize

os.write(logfd, '-------------------------------------------\n')
os.write(logfd, 'There are the multiple provide bellow:\n')
for key in provide_map.keys():
    if len(provide_map[key]) > 1:
        os.write( logfd, '%s: %s\n' % (key, str(provide_map[key])) )
os.write(logfd, '-------------------------------------------\n')

title = '#!/usr/bin/python\n\npackages_infor =\\\n'

os.write(outfd, title + print_rpmfn_map())

if use_script_in_dep:
    os.write(outfd, '\n\n' + print_script_in_dep())

if outfd > 2:
   os.close(outfd)
if logfd > 2:
   os.close(logfd)
