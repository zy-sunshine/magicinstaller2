### -*- python -*-
# Copyright (C) 2010, zy_sunshine.
# Author:   zy_sunshine <zy.netsec@gmail.com>
# All rights reserved.

Import('env', '_p', '_inc', '_my_dir', '_error')
Import('TOPDIR', 'BUILD_SYSTEM')

import sys
import os
import types

### Command line and Config
#get specdir
specdir = ARGUMENTS.get('specdir', _p(TOPDIR, 'spec'))
if specdir != '':
    sys.path.insert(0, specdir)

import mi_config
mi_config.specdir = specdir
mi_config.sifile = os.path.join(specdir, 'specinfo.py')

#check rpmtype
if mi_config.pkgtype not in ['rpm', 'tar']:
    print "Only rpm and tar are supported in pkgtype."
    sys.exit(1)

#get pkgdirs
for pd in mi_config.pkgdirs.split(':'):
    if not os.path.isdir(_p(TOPDIR, pd)):
        print "%s is not a directory" % pd
        sys.exit(1)

#get debug option
debugopts = ARGUMENTS.get('debug', None)
if debugopts:
    debugopts = string.split(debugopts, ':')
else:
    debugopts = []
mi_config.debugopts = debugopts

### Base Environment
env['MI_BASE_VARS'] = []
for k in mi_config.__dict__:
    if k[:2] != '__' and type(mi_config.__dict__[k]) \
        in (types.BooleanType, types.IntType, types.StringType, types.ListType, types.TupleType):
        env[k] = mi_config.__dict__[k]
        env['MI_BASE_VARS'].append(k)

### Scon Utils
def depInstallDir(env, alias, destdir, srcdirs):
    '''
    destdir<str> is the target directory which will be installed source directories in.
    srcdirs<list> is the list of source directories.
    '''
    def getAllExcludeSvnFile(dir):
        allfiles = []
        topdown = True
        for root, dirs, files in os.walk(dir, topdown):
            for d in dirs:
                if d == '.svn':
                    dirs.remove(d)
            for f in files:
                allfiles.append(os.path.join(root, f))
        return  allfiles

    allfiles = []
    for srcd in srcdirs:
        files = []
        srcd = os.path.abspath(srcd)
        if not os.path.isdir(srcd):
            # Omit the file, Only deal with directory.
            continue
        else:
            files = getAllExcludeSvnFile(srcd)
            files
        allfiles.extend(files)
        for f in files:
            related_dir = os.path.dirname(f)[len(srcd):]
            env.Alias(target=alias, 
                    source=env.Install(os.path.join(destdir, os.path.basename(srcd), 
                                       related_dir.lstrip('/')), f))
    return allfiles

def depInstall(env, alias, destdir, files):
    env.Alias(target=alias, source=env.Install(destdir, files))

def depInstallAs(env, alias, destfile, file):
    env.Alias(target=alias, source=env.InstallAs(destfile, file))

def depPyModule(env, alias, dir, sofile, cfiles):
    sopath = os.path.join(mi_config.destdir, mi_config.pythondir, 'site-packages', sofile)
    env.Command(sopath, cfiles,
                ['cd %s; %s setup.py install --prefix=%s/usr' % \
                 (dir, mi_config.pythonbin, mi_config.pyextdir)])
    env.Alias(alias, sopath)
    #env.Depends(alias, sopath)

# python compiler
def pycompiler(source, target, env):
    import py_compile
    for src in source:
        py_compile.compile(str(src))
pycbuilder = Builder(action=pycompiler)
env['BUILDERS']['PYCBuilder'] = pycbuilder

##### Common Function and Class.
def DirValue(dir_or_list, env=env):
    def file_stat(arg, dirname, namelist):
        namelist.sort()
        for name in namelist:
            fullname = os.path.join(dirname, name)
            lst = os.lstat(fullname)
            arg.append((fullname, lst.st_size, lst.st_mtime))
            #arg.append((fullname, lst.st_mode, lst.st_dev,
            #            lst.st_uid, lst.st_gid, lst.st_size, lst.st_mtime))
    if type(dir_or_list) is types.ListType:
        dir_list = dir_or_list
    else:
        dir_list = [dir_or_list]
    dir_value = []
    for dir in dir_list:
        os.path.walk(dir, file_stat, dir_value)
    return env.Value(dir_value)

### Scon Maker
import PkgMaker

class MiPkgMaker(PkgMaker.BinPkgMaker):
    source_prefix = '#bindir/src'
    build_root = mi_config.devrootdir
    pack_prefix = '#bindir'

def getSudoSh(cmd):
    if os.getuid() != 0:
        return 'sudo sh -c "%s" $sudoprom' % cmd
    else:
        return cmd

Export('env')
Export('mi_config')
Export('depInstall', 'depInstallAs', 'depPyModule', 'depInstallDir')
Export('DirValue')
Export('PkgMaker', 'MiPkgMaker')
Export('getSudoSh')

# ##### Construct the magicinstaller main application, tar into :
# #       #bindir/root.src.tar.gz         (source file)
# #       #bindir/root.src.etc.tar.gz     (config file)
# #       needed by rootfs .
# WITH_MI = os.path.exists('.with_mi')
# WITH_FS = os.path.exists('.with_fs')
# WITH_ISO = os.path.exists('.with_iso')

# Export('WITH_MI', 'WITH_FS', 'WITH_ISO')

# if WITH_MI:
#     SConscript('SConstruct-mi')

# ##### Construct the mirootfs, tar into :
# #       #bindir/mirootfs.gz
# #       #bindir/mi-vmlinuz-x.xx.xx
# if WITH_FS:
#     SConscript('SConstruct-rootfs')

# ##### Construct the target iso file, need :
# #       #bindir/mi-vmlinuz-x.xx.xx      (kernel file)
# #       #bindir/mirootfs.gz             (initrd file)
# if WITH_ISO:
#     SConscript('SConstruct-iso')

