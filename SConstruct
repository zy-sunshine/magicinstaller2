### -*- python -*-
# Copyright (C) 2010, zy_sunshine.
# Author:   zy_sunshine <zy.netsec@gmail.com>
# All rights reserved.

import sys
import os
import types

if '$specdir' != '':
    sys.path.insert(0, '$specdir')
sys.path.insert(0, 'scripts')

env = Environment()
import mi_config
import PkgMaker
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

#get debug option
debugopts = ARGUMENTS.get('debug', None)
if debugopts:
    debugopts = string.split(debugopts, ':')
else:
    debugopts = []
mi_config.debugopts = debugopts

### Base Environment
env = Environment()
for k in mi_config.__dict__:
    if k[:2] != '__' and type(mi_config.__dict__[k]) \
        in (types.BooleanType, types.IntType, types.StringType):
        env[k] = mi_config.__dict__[k]

### Scon Utils
def depInstall(env, alias, destdir, files):
    env.Alias(target=alias, source=env.Install(destdir, files))

def depInstallAs(env, alias, destfile, file):
    env.Alias(target=alias, source=env.InstallAs(destfile, file))

def depPyModule(env, alias, dir, sofile, cfiles):
    sopath = os.path.join(mi_config.destdir, mi_config.pythondir, 'site-packages', sofile)
    env.Command(sopath, ['setup.py'] + cfiles,
                ['cd %s; %s setup.py install --prefix=%s/usr' % \
                 (dir, mi_config.pythonbin, mi_config.destdir)])
    env.Alias(alias, sopath)
    #env.Depends(alias, sopath)

Export('env')
Export('mi_config')
Export('depInstall', 'depInstallAs', 'depPyModule')
Export('PkgMaker')

##### Construct the magicinstaller main application, tar into :
#       #bindir/root.src.tar.gz         (source file)
#       #bindir/root.src.etc.tar.gz     (config file)
#       needed by rootfs .
#SConscript('SConstruct-mi')

##### Construct the mirootfs, tar into :
#       #bindir/mirootfs.gz
#       #bindir/mi-vmlinuz-x.xx.xx
SConscript('SConstruct-rootfs')

##### Construct the target iso file, need :
#       #bindir/mi-vmlinuz-x.xx.xx      (kernel file)
#       #bindir/mirootfs.gz             (initrd file)
SConscript('SConstruct-iso')

