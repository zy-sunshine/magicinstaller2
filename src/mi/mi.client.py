#!/usr/bin/python
import os, gtk
import gettext
from mi.client.mainwin import MIMainWindow
from mi.client.utils import _, CF, logger
from mi.utils.common import treedir

USE_TEXTDOMAIN = True

## Setup constants and working directory.
logger.info('change current working directory to %s' % os.path.join(CF.D.DATADIR, 'mi'))
build_top = os.environ.get('MI_BUILD_TOP', None)
if build_top:
    os.chdir('%s/src/mi' % build_top)
else:
    os.chdir(os.path.join(CF.D.DATADIR, 'mi'))

if USE_TEXTDOMAIN:
    sys_locale = '/usr/share/locale'
    all_dirs, all_files = treedir(sys_locale, False)
    textdomain = CF.D.TEXTDOMAIN
    if textdomain+'.mo' in all_files:
        gettext.bindtextdomain(textdomain, sys_locale)
        gettext.textdomain(textdomain)
    else:
        logger.w('Can not bind textdomain %s' % textdomain)

## We can use some custom style here.
#settings = gtk.settings_get_default()
#settings.set_string_property('gtk-theme-name', 'Default', '')
#gtk.rc_parse_string(open('style.rc', 'rt').read())
#print gtk.rc_get_theme_dir()
settings = gtk.settings_get_default()
settings.set_string_property("gtk-theme-name", "Gnursid", "")

step_name_list = (
    (_('Welcome'), 'welcome'), # (group name, module name)
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
win.set_size_request(CF.D.FULL_WIDTH, CF.D.FULL_HEIGHT)
win.set_resizable(False)
win.init()

win.show()

root = gtk.gdk.get_default_root_window()
cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
root.set_cursor(cursor)

gtk.main()
