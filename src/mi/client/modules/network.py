# -*- python -*-
from mi.client.utils import _
from mi.client.utils import magicstep

class MIStep_network (magicstep.magicstep):
    NAME = 'network'
    LABEL = _("Network")
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'network.xml')

    def get_label(self):
        return self.LABEL

    def check_ready(self):
        return  1
