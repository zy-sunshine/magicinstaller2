#!/usr/bin/python
from miui.utils import _
from miui.utils import magicstep

class MIStep_testops (magicstep.magicstep):
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'testops.xml')

    def get_label(self):
        return  _("Test")

    def btnback_clicked(self, widget, data):
        return  1

    def btnnext_clicked(self, widget, data):
        return  1

    def startsleep(self, widget, data):
        self.name_map['sleepbtn'].set_sensitive(False)
        self.rootobj.tm.add_action('Test Op: Sleep', self.stopsleep, None, 'sleep', 5)

    def stopsleep(self, tdata, data):
        self.name_map['sleepbtn'].set_sensitive(True)
