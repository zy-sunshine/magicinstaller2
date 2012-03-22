#!/usr/bin/python
import gtk
from miui import _
from miui.leftpanel import MILeftPanel
from miui.rightpanel import MIRightPanel
from miui.top import MITop
from miui.bottom import MIBottom
from miui.modules import *
from xml.dom.minidom import parse
from miutil import search_file
from miconfig import MiConfig

CONF = MiConfig.get_instance()

class MIMainWindow(gtk.Window):
    def __init__(self, *args, **kw):
        gtk.Window.__init__(self, *args, **kw)
        self.set_name(self.__class__.__name__)
        self.leftpanel = MILeftPanel(self)
        self.rightpanel = MIRightPanel(self)
        self.set_title(_('Magic Installer'))
        self.set_border_width(4)
        self.connect('destroy', lambda x: gtk.main_quit())
        self.values = parse(search_file('magic.values.xml', [CONF.hotfixdir, '.']))

    def init(self):
        self.step_lst = [ ('welcome', MIStep_welcome(self), _('Welcome')),
            #('scsi', MIStep_scsi()),
            ('pkgselect', MIStep_pkgselect(self), _('Select Package')),
            ('parted', MIStep_parted(self), _('Partition')),
            ('bootloader', MIStep_bootloader(self), _('Set Bootloader')),
            ('takeactions', MIStep_takeactions(self), _('Install Pacakges')),
            ('startsetup', MIStep_startsetup(self), _('Start Setup')),
            ('accounts', MIStep_accounts(self), _('Set Account')),
            ('Xwindow', MIStep_Xwindow(self), _('Xwindow Configuration')),
            ('dosetup', MIStep_dosetup(self), _('Make Setup Effect')),
            ('finish', MIStep_finish(self), _('Install Finished')),
        ]
        
        image = get.Image()
        image.set_from_file('images/applet-blank.png')
        for step in step_lst:
            #step[2]
            btn = gtk.Button()
            btn.add(image)
            self.leftpanel.add(btn)


