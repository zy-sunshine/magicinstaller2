# -*- python -*-
from miui.utils import _
from miui.utils import magicstep

class MIStep_mouse (magicstep.magicstep):
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'mouse.xml')

    def get_label(self):
        return  _("Mouse")

    def check_ready(self):
        return  1
