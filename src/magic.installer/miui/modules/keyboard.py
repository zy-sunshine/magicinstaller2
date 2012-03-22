# -*- python -*-
from miui import _
from miui.utils import magicstep

class MIStep_keyboard (magicstep.magicstep):
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'keyboard.xml')

    def get_label(self):
        return  _("Keyboard")

    def check_ready(self):
        return  1
