#!/usr/bin/python
import os, gtk
from mi.client.mainwin import MIMainWindow
from mi.client.utils import _, CF, logger

## Setup constants and working directory.
logger.info('change current working directory to %s' % CF.D.DATADIR)
os.chdir(CF.D.DATADIR)

settings = gtk.settings_get_default()
#settings.set_string_property('gtk-theme-name', 'Default', '')
#gtk.rc_parse_string(open('style.rc', 'rt').read())
#print gtk.rc_get_theme_dir()

step_name_list = (
    (_('Welcome'), 'welcome'),
    #'scsi',
    (_('Package'), 'pkgselect'),
    (_('Partition'), 'partition'),
    (_('Partition'), 'dopartition'),
    #(_('Setup'), 'startsetup'),
    (_('Setup'), 'accounts'),
    #'Xwindow',
    (_('Setup'), 'bootloader'),
    (_('Setup'), 'takeactions'),
    #(_('Setup'), 'dosetup'),
    (_('Finish'), 'finish')
    )
win = MIMainWindow(step_name_list, gtk.WINDOW_TOPLEVEL)
win.init()

win.show()

gtk.main()
