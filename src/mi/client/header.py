#!/usr/bin/python
import gtk

class MIHeader(gtk.HBox):
    def __init__(self, sself, *args, **kw):
        gtk.HBox.__init__(self, *args, **kw)
        self.sself = sself
        self.banner_img = gtk.Image()
        self.banner_img.set_from_file('images/banner.png')
        self.pack_start(self.banner_img, True, True)

    
    def set_logo(self, logo):
        self.banner_img.set_from_file(logo)
    
    
        