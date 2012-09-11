import os, gtk
from mi.client.mainwin import MIMainWindow
from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()

from mi.utils import logger

## Setup constants and working directory.
<<<<<<< HEAD
logger.info('change current working directory to %s' % CONF.LOAD.CONF_DATADIR)
os.chdir(CONF.LOAD.CONF_DATADIR)
step_name_list = ('welcome',
    #'scsi',
    'partition',
    'bootloader',
    'pkgselect',
    'takeactions',
    'startsetup',
    'accounts',
    'Xwindow',
    'dosetup',
    'finish')
win = MIMainWindow(gtk.WINDOW_TOPLEVEL, step_name_list)
=======
logger.info('change current working directory to %s' % CF.D.DATADIR)
os.chdir(CF.D.DATADIR)

win = MIMainWindow(gtk.WINDOW_TOPLEVEL)
>>>>>>> Update
win.init()
#win.show_all()
win.show()

gtk.main()
