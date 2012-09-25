import os, gtk
from mi.client.mainwin import MIMainWindow
from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()

from mi.utils import logger

## Setup constants and working directory.
logger.info('change current working directory to %s' % CF.D.DATADIR)
os.chdir(CF.D.DATADIR)
step_name_list = ('welcome',
    #'scsi',
    'pkgselect',
    'partition',
    'dopartition',
    #'takeactions',
    'startsetup',
    'accounts',
    #'Xwindow',
    'bootloader',
    'dosetup',
    'finish')
win = MIMainWindow(step_name_list, gtk.WINDOW_TOPLEVEL)
win.init()

win.show()

gtk.main()
