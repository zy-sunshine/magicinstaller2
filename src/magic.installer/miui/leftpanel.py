#!/usr/bin/python
import gtk

class MILeftPanel(gtk.VBox):
    def __init__(self, sself, *args, **kw):
        gtk.VBox.__init__(self, *args, **kw)
        self.sself = sself

