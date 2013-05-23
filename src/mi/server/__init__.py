import os, sys, glob
registers_map = {}
#CURDIR = os.path.dirname(os.path.realpath(__file__))
#for fpath in glob.glob(CURDIR+'/operations/*.py') + glob.glob(CURDIR+'/operations/actions/*.py'):
#    fn = os.path.basename(fpath)
#    mod = os.path.splitext(fn)[0]
#    if mod != '__init__':
#        exec('from operations import %s' % mod)
#        exec('registers_map["%s"] = %s.register' % (mod, mod))
#        #eval('__import__("welcome")')
import types
CURDIR = os.path.dirname(os.path.realpath(__file__))

from mi.utils.miregister import MiRegister
module_list = []
# It will cause execute this file twice
#import mi.client.modules #@UnresolvedImport
import imp, pkgutil
for importer, modname, ispkg in pkgutil.iter_modules([os.path.join(CURDIR, 'operations'), os.path.join(CURDIR, 'operations', 'actions')]):
    if ispkg:
        continue
    fpath = os.path.join(importer.path, modname) + '.py'
    mod = imp.load_source(modname, fpath)
    for k in dir(mod):
        m = getattr(mod, k)
        if type(m) != types.ClassType:
            if isinstance(m, MiRegister):
                #module_list.append(m)
                registers_map[fpath] = m
                break # Only get first instance

handlers_long = {}
handlers_short = {}

def merge_handlers(_from, _to):
    for name, func_lst in _from.items():
        if len(func_lst) > 1:
            raise Exception('Import server handlers Error', 'Too many handler \
            functions (%s count) on one handler %s' % (len(func_lst), name))
        if len(func_lst) == 1:
            _to[name] = func_lst[0]
        else:
            raise Exception('Import server handlers Error', 'Empty handler \
            function list??? on handler %s' % name)

for v in registers_map.values():
    merge_handlers(v['long'], handlers_long)
    merge_handlers(v['short'], handlers_short)

from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()

if __name__ == '__main__':
    print '\nregister_map:\n'
    print registers_map
    print '\nhandlers_long:\n'
    print handlers_long
    print '\nhandlers_short:\n'
    print handlers_short

