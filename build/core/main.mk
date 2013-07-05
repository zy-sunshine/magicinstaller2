import os, sys
env = Environment()
env['PRODUCTS'] = {}
env['DEVICES'] = {}
def _p(*args):
    return os.path.join(*args)

def _inc(*args):
    if len(args) == 1:
        if type(args[0]) is str:
            SConscript(args[0])

        if type(args[0]) is list or type(args[0]) is tuple:
            for f in args[0]:
                SConscript(f)
    else:
        SConscript(_p(*args))

def _my_dir():
    return os.path.abspath(os.path.curdir)

def _error(msg):
    raise Exception(msg)

def _get_var_by_product(target_product, var_name):
    for name, product in env['PRODUCTS'].items():
        if name == target_product:
            return product.get(var_name)
    return None

Export('env', '_p', '_inc', '_my_dir', '_error', '_get_var_by_product')
TOPDIR = os.environ.get('MI_BUILD_TOP')
if not TOPDIR:
    TOPDIR = os.path.abspath(os.path.curdir)
    TOPDIR = os.path.dirname(os.path.dirname(TOPDIR))

BUILD_SYSTEM = _p(TOPDIR, 'build/core')

Export('TOPDIR', 'BUILD_SYSTEM')

### mainly set all variable into env of SCons, and some SCons install function encapsulation.
_inc(BUILD_SYSTEM, 'oldconfig.mk')

### export variables for SCons scripts build branch control.
_inc(BUILD_SYSTEM, 'defines.mk')

## config.mk will export some varibales for SConscripts envsetup.mk and then include 
## envsetup.mk file.
## envsetup.mk script will export some varialbes for product_config.mk and then include
## version_defaults.mk *product_config.mk. These are the main framework of Makefile from 
## android. The tactics will be invoked in product_config.mk <- vendor/*/*/MiProducts.mk
## 
## Note: we remove the BoardConfig.mk include in config.mk, because we do not have a target
## board to run our rootfs, we must run our rootfs on all the x86/amd64 computers.
_inc(BUILD_SYSTEM, 'config.mk')

def get_sconscripts(dir, topdown=True):
    scripts = []
    for root, dirs, files in os.walk(dir, topdown):
        if 'SConscript' in files:
            scripts.append(os.path.join(root, 'SConscript'))
            dirs[:] = []
    return scripts

Import('TARGET_PRODUCT')

def _get_cur_product_var(var_name):
    return _get_var_by_product(TARGET_PRODUCT, var_name)

Export('_get_cur_product_var')

## Historical issue include some SConscripts in TOPDIR, it is conveniently for pack packages.
_inc(TOPDIR, 'SConscript-main')

## Search all "SConscipt" in each directory branch top down, if find a "SConscript" we do not
## search other in its subdirectories, on the other hand the toppest SConscript has to include
## other SConscripts in its subdirectories.
scripts = get_sconscripts(TOPDIR)
_inc(scripts)

