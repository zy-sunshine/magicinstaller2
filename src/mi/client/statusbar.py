#!/usr/bin/python
import gtk

class MIStatusBar(gtk.HBox):
    def __init__(self, sself, *args, **kw):
        gtk.HBox.__init__(self, *args, **kw)
        self.sself = sself
        self.tasks = []
        arrowup = gtk.Arrow(gtk.ARROW_UP, gtk.SHADOW_OUT)
        arrowdown = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_OUT)
        self.progress = gtk.ProgressBar()

        self.set_border_width(2)
        self.set_spacing(2)
        self.pack_start(arrowup, False, True)
        self.pack_start(arrowdown, False, True)
        self.pack_start(self.progress, True, True)
        self.show_all()
    def get_progressbar(self):
        return self.progress
    