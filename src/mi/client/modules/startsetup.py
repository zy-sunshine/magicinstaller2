#!/usr/bin/python
from mi.client.utils import _
from mi.client.utils import magicstep
from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()

from mi.server.utils import logger
dolog = logger.info

class MIStep_startsetup (magicstep.magicstep):
    NAME = 'startsetup'
    LABEL = _("Start to setup")
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'startsetup.xml', 'startsetup')

    def get_label(self):
        return self.LABEL
        
    def btnnext_clicked(self, widget, data):
        # We add a skip step name to current class, 
        # and it will remove the step in magic.installer class
        self.fetch_values(self.rootobj.values,
                valuename_list = ['startsetup.skipXsetting'])
        skipx = self.get_data(self.values, 'startsetup.skipXsetting')
        if skipx == '1':
            self.skip_stepnames.append('Xwindow')
            CF.G.skipxsetting = 1
        else:
            CF.G.skipxsetting = 0
        return  1
