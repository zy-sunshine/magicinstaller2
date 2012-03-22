import os
import glob
from miui.utils import magicstep
CURDIR = os.path.dirname(os.path.realpath(__file__))
for fpath in glob.glob(CURDIR+'/*.py'):
    fn = os.path.basename(fpath)
    mod = os.path.splitext(fn)[0]
    if mod != '__init__':
        exec('from %s import MIStep_%s' % (mod, mod))
        #eval('__import__("welcome")')

