#!/usr/bin/python
from mi.client.utils import _, magicpopup
from mi.client.utils import magicstep

class MIStep_finish (magicstep.magicstep):
    NAME = 'finish'
    LABEL = _("Finish")
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'finish.xml', 'finish')
        rootobj.btnnext_sensitive(False)
        rootobj.btnback_sensitive(False)

    def get_label(self):
        return self.LABEL

    def btnfinish_clicked(self, widget, data):
        self.default_btnfinish_clicked(widget, data)

    def leave(self):
        magicpopup.magicmsgbox(None, _('You can not go back because the installation has finished.'),
                               magicpopup.magicmsgbox.MB_ERROR,
                               magicpopup.magicpopup.MB_OK)
        return 0

if __name__ == '__main__':
    import gtk
    from mi.client.mainwin import MIMainWindow
    win = MIMainWindow(gtk.WINDOW_TOPLEVEL)
    win.init()
    #win.show_all()
    win.show()
    
    gtk.main()
