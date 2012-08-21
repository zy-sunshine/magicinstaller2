# -*- python -*-
from mi.client.utils import _
from mi.client.utils import magicstep

class MIStep_network (magicstep.magicstep):
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'network.xml')

    def get_label(self):
        return  _("Network")

    def check_ready(self):
        return  1
