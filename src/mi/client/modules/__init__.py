# Method 1
#import os
#import glob
#from mi.client.utils import magicstep
#CURDIR = os.path.dirname(os.path.realpath(__file__))
#for fpath in glob.glob(CURDIR+'/*.py'):
#    fn = os.path.basename(fpath)
#    mod = os.path.splitext(fn)[0]
#    if mod != '__init__':
#        exec('from %s import MIStep_%s' % (mod, mod))

# Method 2
import os, sys
import types
CURDIR = os.path.dirname(os.path.realpath(__file__))

from mi.client.utils.magicstep import magicstep, magicstepgroup
module_list = []
# It will cause execute this file twice
#import mi.client.modules #@UnresolvedImport
import imp, pkgutil
for importer, modname, ispkg in pkgutil.iter_modules([CURDIR]):
    if ispkg:
        continue
    fpath = os.path.join(CURDIR, modname) + '.py'
    # It will import mi.client.modules by needed.
    #mod = imp.load_source('mi.client.modules.'+modname, fpath)
    mod = imp.load_source(modname, fpath)
    for k in dir(mod):
        m = getattr(mod, k)
        if type(m) == types.ClassType and \
                    m is not magicstep and \
                    m is not magicstepgroup:
            if issubclass(m, magicstep):
                module_list.append(m)
                break # Only get first class matched

# Method 3
#import imp, pkgutil
#for importer, modname, ispkg in pkgutil.iter_modules([CURDIR]):
#    if ispkg:
#        continue
#    fpath = os.path.join(CURDIR, modname) + '.py'
#    l_map = {}
#    execfile(fpath, l_map, l_map)
#    for k, m in l_map.items():
#        if type(m) == types.ClassType and \
#                    m is not magicstep and \
#                    m is not magicstepgroup:
#            if issubclass(m, magicstep):
#                print m
#                break # Only get first class matched
