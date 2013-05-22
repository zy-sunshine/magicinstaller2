import os
env = Environment()
def _p(*args):
    return os.path.join(*args)

def _inc(*args):
    SConscript(_p(*args))

def _my_dir():
    return os.path.abspath(os.path.curdir)

Export('env', '_p', '_inc', '_my_dir')
TOPDIR = os.environ.get('MI_BUILD_TOP')
if not TOPDIR:
    TOPDIR = os.path.abspath(os.path.curdir)
    TOPDIR = os.path.dirname(os.path.dirname(TOPDIR))

BUILD_SYSTEM = _p(TOPDIR, 'build/core')

Export('TOPDIR', 'BUILD_SYSTEM')

_inc(BUILD_SYSTEM, 'config.mk')

