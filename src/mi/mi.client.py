#!/usr/bin/python
import os, gtk
from mi.client.mainwin import MIMainWindow
from mi.client.utils import _, CF, logger
from mi.utils.common import treedir

USE_TEXTDOMAIN = True

## Setup constants and working directory.
logger.info('change current working directory to %s' % CF.D.DATADIR)
build_top = os.environ.get('MI_BUILD_TOP', None)
if build_top:
    os.chdir('%s/src/mi' % build_top)
else:
    os.chdir(CF.D.DATADIR)

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
