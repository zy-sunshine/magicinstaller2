#!/usr/bin/python
import gtk

class MIRightPanel(gtk.Frame):
    def __init__(self, sself, *args, **kw):
        gtk.Frame.__init__(self, *args, **kw)
        self.sself = sself
        self.set_size_request(600, 500)
        self.curwidget = None

    def switch(self, widget):
        if self.curwidget is not None:
            self.remove(self.curwidget)
            self.curwidget = widget
            self.curwidget.show_all()
            self.add(self.curwidget)
