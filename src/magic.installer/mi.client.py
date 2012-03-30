import os, gtk
from miui.mainwin import MIMainWindow
from miutils.miconfig import MiConfig
CONF = MiConfig.get_instance()
from miutils.milogger import ClientLogger
log = ClientLogger.get_instance(ClientLogger, __name__)

# Setup constants and working directory.
log.i('change current working directory to %s' % CONF.LOAD.CONF_DATADIR)
os.chdir(CONF.LOAD.CONF_DATADIR)

win = MIMainWindow(gtk.WINDOW_TOPLEVEL)
win.init()
#win.show_all()
win.show()

gtk.main()

ClientLogger.del_instances(ClientLogger)
