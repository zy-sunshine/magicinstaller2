import os
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

_inc(BUILD_SYSTEM, 'config.mk')

