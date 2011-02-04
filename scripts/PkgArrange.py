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
import sys
import types

from getopt import getopt

import pkgpublic

# Usage:
#   PkgArrange.py [-o outputfn] [-l logfn]

# Sort packages by the dependency of pre_in post_in satisfaction.
use_script_in_dep = False
# Get every package's weight number and print it out in pkgarr.py .
use_weight_number = False
# sort the package by the basepkg_list in mi_config.
use_sort_by_base_pkg = True

if use_script_in_dep:
    try:
        from pkginfor import script_in_dep
    except ImportError:
        sys.path.insert(0, 'tmp')
        from pkginfor import script_in_dep

try:
    from pkginfor import packages_infor
except ImportError:
    sys.path.insert(0, 'tmp')
    from pkginfor import packages_infor

sys.path.insert(0, '')
sys.path.insert(0, 'spec')
import mi_config

volume_limit_list   = mi_config.volume_limit_list
placement_list      = mi_config.placement_list
toplevel_groups     = mi_config.toplevel_groups
add_deps            = mi_config.add_deps
remove_deps         = mi_config.remove_deps
basepkg_list        = mi_config.basepkg_list

# To resolve the loop dependency, there are two method.
# The first is use remove_deps to broke the loop. This method can control the
#  consequence of the package but lost dependency link. So group make must
#  remember to include them both or do not include any one.
# The second method is leave the loop dependency for this script. The
#  dependency link is reserved, but the packages consequence is random...


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

def add_rm_dep(packages_infor, depnum):
    # Adjust dependencies according to add_deps, remove_deps
    adjdeps_map = {}
    for k in add_deps.keys():
        adjdeps_map[k] = 'y'
    for k in remove_deps.keys():
        adjdeps_map[k] = 'y'
    for pkg in adjdeps_map.keys():
        add_map = {}
        remove_map = {}
        if add_deps.has_key(pkg):
            for dep in add_deps[pkg]:
                add_map[dep] = 'y'
        if remove_deps.has_key(pkg):
            for dep in remove_deps[pkg]:
                remove_map[dep] = 'y'
        if packages_infor.has_key(pkg):
            for dep in packages_infor[pkg][depnum]:
                if not remove_map.has_key(dep):
                    add_map[dep] = 'y'
            packages_infor[pkg][depnum] = add_map.keys()
add_rm_dep(packages_infor, pkgpublic.deps)
if use_script_in_dep:
    add_rm_dep(script_in_dep, 0)

#-------------------------------------------------------
def get_pkg_weight_number(packages_infor, depnum):
    # Increase the weight number of each pkg by every pkg's dependency
    packages_weight_number = {}
    for pkgfn in packages_infor.keys():
        topdeps = packages_infor[pkgfn][depnum]
        curdeplist = []
        for dep in topdeps:
            curdeplist.append((dep, []))
        subdeps_map = {}
        loopdeps_map = {}
        while curdeplist != []:
            newdeplist = []
            for (dep, deppath) in curdeplist:
                newdeppath = deppath + [dep]
                if dep == pkgfn:
                    #os.write(logfd, 'LoopDep: %s\n' % str(newdeppath))
                    for d in deppath:
                        loopdeps_map[d] = 'y'
                    continue # Do not go more on loop dependency.
                if not packages_infor.has_key(dep):
                    continue
                depdeplist = packages_infor[dep][depnum]
                for depdep in depdeplist:
                    if subdeps_map.has_key(depdep):
                        continue
                    if deppath != [] and depdep in topdeps:
                        #print pkgfn, newdeppath, depdep
                        continue
                    newdeplist.append((depdep, newdeppath))
                    subdeps_map[depdep] = str(newdeppath)
            curdeplist = newdeplist
        import copy
        all_dep_pkg = []
        all_dep_pkg = copy.deepcopy(subdeps_map.keys())
        all_dep_pkg.extend(topdeps)
        all_dep_pkg = list(set(all_dep_pkg))
        for pkg in all_dep_pkg:
            if packages_weight_number.has_key(pkg):
                packages_weight_number[pkg] += 1
            else:
                packages_weight_number[pkg] = 1
        del(subdeps_map) # Release the space occupied by subdeps_map.
    return packages_weight_number
#---------- 
# notice: we calculate each package's weight number according to 
#           the number of being depended by other packages.
#         But we have not use this element to adjust the order of packages.
#-----------
if use_weight_number:
    packages_weight_number = get_pkg_weight_number(packages_infor, pkgpublic.deps)

#---------------------------------------------------------

def break_loop(packages_infor, depnum):
    # Remove the bypass dependencies in packages_infor.
    for pkgfn in packages_infor.keys():
        topdeps = packages_infor[pkgfn][depnum]
        curdeplist = []
        for dep in topdeps:
            curdeplist.append((dep, []))
        subdeps_map = {}
        loopdeps_map = {}
        while curdeplist != []:
            newdeplist = []
            for (dep, deppath) in curdeplist:
                newdeppath = deppath + [dep]
                if dep == pkgfn:
                    os.write(logfd, 'LoopDep: %s\n' % str(newdeppath))
                    for d in deppath:
                        loopdeps_map[d] = 'y'
                    continue # Do not go more on loop dependency.
                if not packages_infor.has_key(dep):
                    continue
                depdeplist = packages_infor[dep][depnum]
                for depdep in depdeplist:
                    if subdeps_map.has_key(depdep):
                        continue
                    if deppath != [] and depdep in topdeps:
                        #print pkgfn, newdeppath, depdep
                        continue
                    newdeplist.append((depdep, newdeppath))
                    subdeps_map[depdep] = str(newdeppath)
            curdeplist = newdeplist
        newtopdeps = []
        # Loop Dependency should be reserved.
        for dep in loopdeps_map.keys():
            if dep != pkgfn:
                newtopdeps.append(dep)
        for dep in topdeps:
            if loopdeps_map.has_key(dep):
                continue
            if subdeps_map.has_key(dep):
                os.write(logfd, '%s is removed from the deplist of %s because %s.\n' % (dep, pkgfn, subdeps_map[dep]))
                continue
            newtopdeps.append(dep)
        packages_infor[pkgfn][depnum] = newtopdeps
        del(subdeps_map) # Release the space occupied by subdeps_map.
    return packages_infor
os.write(logfd, '\n\n-------------------------------------------------\n')
os.write(logfd, '***break loop dependency of packages_infor****\n')
packages_infor = break_loop(packages_infor, pkgpublic.deps)
os.write(logfd, '\n\n-------------------------------------------------\n')
if use_script_in_dep:
    os.write(logfd, '***break loop dependency of script_in_dep****\n')
    script_in_dep = break_loop(script_in_dep, 0)
    os.write(logfd, '\n-------------------------------------------------\n')

# Sort according dependency.
minset_list = []
minset_map = {}

def get_pkg_name(pkg):
    pkgname = ''
    try:
        pkgname = pkg[ : pkg.rindex('-') ]
        pkgname = pkg[ : pkgname.rindex('-') ]
    except ValueError, e:
        print 'Can not get the name of %s Error: %s' % (pkg, str(e))
        return pkg
    return pkgname

def sort_by_basepkg(sort_list, base_list):
    if base_list == []:
        return sort_list
    sorted_list = []
    for name in base_list:
        for pkg in sort_list:
            if name == get_pkg_name(pkg):
                sorted_list.append(pkg)
    remain_list = list(set(sort_list)-set(sorted_list))
    sorted_list.extend(remain_list)
    return sorted_list

def sort_by_dep(pkglist, packages_infor, depnum, curmap):
    # pkglist might be duplicated but curmap can skip it.
    if pkglist == []:
        return []
    result = []
    for pkg in pkglist:
        if minset_map.has_key(pkg):
            continue
        if curmap.has_key(pkg):
            continue
        curmap[pkg] = 'y'
        if not packages_infor.has_key(pkg):
            pkgdeplist = []
        else:
            pkgdeplist = packages_infor[pkg][depnum]
        result = result + sort_by_dep(pkgdeplist, packages_infor, depnum, curmap) + [pkg]
    return result
#----------------------------
# First Sort
for placement in placement_list:
    # We can only sort by basepkg in first time, because it will break the order.
    if use_sort_by_base_pkg:
        placement = sort_by_basepkg(placement, basepkg_list)
    result_list = sort_by_dep(placement, packages_infor, pkgpublic.deps, {})
    minset_list.append(result_list)
    for result in result_list:
        minset_map[result] = 'y'

# Search all packages that are not arrange yet.
last_list = []
for pkgfn in packages_infor.keys():
    if minset_map.has_key(pkgfn):
        continue
    last_list.append(pkgfn)

# We can only sort by basepkg in first time, because it will break the order.
if use_sort_by_base_pkg:
    last_list = sort_by_basepkg(last_list, basepkg_list)
result_list = sort_by_dep(last_list, packages_infor, pkgpublic.deps, {})
minset_list.append(result_list)
#---------------------------
# Second Sort
# clean the minset_map firstly
minset_map.clear()

if use_script_in_dep:
    for s in range(len(minset_list)):
        minset_list[s] = sort_by_dep(minset_list[s], script_in_dep, 0, {})

#--------------------------
del(minset_map) # Free the space.

# Now the minset_list contain the minimum set for all placement set.
volume_size = 0
curlist = []
arrangement_list = []
minset_count = 0
volume_count = 0
pkg_count = 0
pkgpos_map = {}

for minset in minset_list:
    for pkgfn in minset:
        pkgsize = packages_infor[pkgfn][pkgpublic.totalsz]
        if volume_size + pkgsize > volume_limit_list[0]:
            if minset_count <= volume_count:
                errmsg = 'Not enough space to place the package "%s" in disc #%d.\n' % (pkgfn, (minset_count + 1))
                os.write(logfd, errmsg)
                if logfd != 2:
                    os.write(2, errmsg)
                sys.exit(1)
            arrangement_list.append(curlist)
            curlist = []
            volume_size = 0
            del volume_limit_list[0]
            volume_count = volume_count + 1
            if volume_limit_list == []:
                errmsg = 'Not enough volume! Broken on %s.\n' % pkgfn
                os.write(logfd, errmsg)
                if logfd != 2:
                    os.write(2, errmsg)
                sys.exit(1)
            pkg_count = 0
        volume_size = volume_size + pkgsize
        curlist.append(packages_infor[pkgfn])
        pkgpos_map[pkgfn] = (volume_count, pkg_count)
        pkg_count = pkg_count + 1
    minset_count = minset_count + 1

if curlist != []:
    arrangement_list.append(curlist)

# Calculate total package size for all arch.
archsize_map = {}
for arch in pkgpublic.arch_map.keys():
    archsize_map[arch] = 0
for arrangement in arrangement_list:
    for pkginfor in arrangement:
        size_map = {}
        noarchsz = -1
        for pkgarch in pkginfor[pkgpublic.pathes]:
            if pkgarch[1] == 'noarch':
                noarchsz = pkgarch[2]
            else:
                size_map[pkgarch[1]] = pkgarch[2]
        if noarchsz >= 0:
            for arch in archsize_map.keys():
                archsize_map[arch] = archsize_map[arch] + noarchsz
        else:
            for arch in archsize_map.keys():
                if size_map.has_key(arch):
                    archsize_map[arch] = archsize_map[arch] + size_map[arch]
                    continue
                for compat in pkgpublic.arch_map[arch]:
                    if size_map.has_key(compat):
                        archsize_map[arch] = archsize_map[arch] + size_map[compat]
                        break

# Output 'arrangement' and 'pkgpos_map' for MagicInstaller.
os.write(outfd, '#!/usr/bin/python\n')

result = 'arch_map = {'
allkeys = pkgpublic.arch_map.keys()
allkeys.sort()
sep = '\n\t'
for arch in allkeys:
    result = result + sep + "'%s' : %s" % (arch, pkgpublic.arch_map[arch])
    sep = ',\n\t'
result = result + ' }\n'
os.write(outfd, result + '\n')

result = 'arrangement = ['
sep = ''
for arrangement in arrangement_list:
    result = result + sep + "\n["
    sep1 = ''
    for pkginfor in arrangement:
        pkgname = os.path.basename(pkginfor[pkgpublic.path][0])
        result = result + sep1 + \
                 "\n\t[%dL, '%s',\n" % (pkginfor[pkgpublic.totalsz], pkgname)
        result = result + "\t\t%s," % str(pkginfor[pkgpublic.group])
        deplist = pkginfor[pkgpublic.deps]
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
        #pathes = pkginfor[pkgpublic.pathes]
        pathes = [pkginfor[pkgpublic.path]]
        if pathes == []:
            result = result + ' []'
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
                    result = result + '],'
        if use_weight_number:
            if packages_weight_number.has_key(pkgname):
                result = result + '\n\t\t%s,' % packages_weight_number[pkgname]
            else:
                result = result + '\n\t\t0,'
        result = result + ']'
        sep1 = ','
    result = result + "]\n"
    sep = ','
result = result + "]\n"
os.write(outfd, result + '\n')

result = 'archsize_map = {'
allkeys = archsize_map.keys()
allkeys.sort()
sep = '\n\t'
for arch in allkeys:
    result = result + sep + "'%s' : %s" % (arch, archsize_map[arch])
    sep = ',\n\t'
result = result + ' }\n'
os.write(outfd, result + '\n')

result = 'pkgpos_map = {'
sep = ''
for pkg in pkgpos_map.keys():
    result = result + sep + "\n\t'%s': %s" % (pkg, str(pkgpos_map[pkg]))
    sep = ','
result = result + '}\n'
os.write(outfd, result + '\n')

toplevelgrp_map = {}
for group in toplevel_groups.keys():
    toplevelgrp_map[group] = {}
    for pkg in toplevel_groups[group]:
        if not pkgpos_map.has_key(pkg):
            # Skip the invalid package.
            continue
        pkglist = [pkg]        
        while pkglist != []:
            newpkglist = []
            for pkg in pkglist:
                if toplevelgrp_map[group].has_key(pkg):
                    continue
                toplevelgrp_map[group][pkg] = 'y'
                (volno, pkgno) = pkgpos_map[pkg]
                pkgdeps = arrangement_list[volno][pkgno][3]
                for pkgdep in pkgdeps:
                    if not toplevelgrp_map[group].has_key(pkgdep):
                        newpkglist.append(pkgdep)
            pkglist = newpkglist

result = 'toplevelgrp_map = {'
sep = ''
for group in toplevelgrp_map.keys():
    result = result + sep + "\n\t'%s': {" % group
    sep1 = ''
    for pkg in toplevelgrp_map[group].keys():
        result = result + sep1 + "\n\t\t'%s': '%s'" % (pkg, group)
        sep1 = ','
    result = result + '}'
    sep = ','
result = result + '}\n'
os.write(outfd, result + '\n')
