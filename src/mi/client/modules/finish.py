#!/usr/bin/python
from mi.client.utils import _, magicpopup
from mi.client.utils import magicstep

class MIStep_finish (magicstep.magicstep):
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'finish.xml', 'finish')

    def get_label(self):
        return _("Finish")

    def btnfinish_clicked(self, widget, data):
        self.default_btnfinish_clicked(widget, data)

    def leave(self):
        magicpopup.magicmsgbox(None, _('You can not go back because the installation has finished.'),
                               magicpopup.magicmsgbox.MB_ERROR,
                               magicpopup.magicpopup.MB_OK)
        return 0
