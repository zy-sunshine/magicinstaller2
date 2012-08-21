import os, gtk
from mi.client.mainwin import MIMainWindow
from mi.utils.miconfig import MiConfig
CONF = MiConfig.get_instance()

#import logging, logging.confg
#logging.config.fileConfig("logging.conf")
#logger = logging.getLogger("mi_client")
#
## Setup constants and working directory.
#logger.info('change current working directory to %s' % CONF.LOAD.CONF_DATADIR)
os.chdir(CONF.LOAD.CONF_DATADIR)

win = MIMainWindow(gtk.WINDOW_TOPLEVEL)
win.init()
#win.show_all()
win.show()

gtk.main()
