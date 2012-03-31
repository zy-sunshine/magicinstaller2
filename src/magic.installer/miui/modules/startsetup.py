#!/usr/bin/python
from miui.utils import _
from miui.utils import magicstep
from miutils.miconfig import MiConfig
CONF = MiConfig.get_instance()

class MIStep_startsetup (magicstep.magicstep):
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'startsetup.xml', 'startsetup')

    def get_label(self):
        return _("Start to setup")
        
    def btnnext_clicked(self, widget, data):
        # We add a skip step name to current class, 
        # and it will remove the step in magic.installer class
        self.fetch_values(self.rootobj.values,
                valuename_list = ['startsetup.skipXsetting'])
        skipx = self.get_data(self.values, 'startsetup.skipXsetting')
        if skipx == '1':
            self.skip_stepnames.append('mistep_Xwindow')
            CONF.RUN.g_skipxsetting = 1
        else:
            skipxsetting = 0
        return  1
