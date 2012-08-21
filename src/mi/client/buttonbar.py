#!/usr/bin/python
import gtk
from mi.client.utils import _

class MIButtonBar(gtk.HBox):
    def __init__(self, sself, *args, **kw):
        gtk.HBox.__init__(self, *args, **kw)
        self.sself = sself
        
        self.logger = gtk.Button()
        self.logger.add(self.img_label_box('images/stock_help_24.png', _('Logger')))
        self.theme = gtk.Button()
        self.theme.add(self.img_label_box('images/gnome-ccthemes-24.png', _('Theme')))
        self.help = gtk.Button()
        self.help.add(self.img_label_box('images/stock_help_24.png', _('Help')))
        self.back = gtk.Button()
        self.back.add(self.img_label_box('images/stock_left_arrow_24.png', _('Back')))
        self.next = gtk.Button()
        self.next.add(self.img_label_box('images/stock_right_arrow_24.png', _('Next')))

        self.set_border_width(4)
        self.set_spacing(4)
        self.pack_start(self.logger, False, True)
        self.pack_start(self.theme, False, True)
        self.pack_start(self.help, False, True)
        
        self.pack_end(self.next, False, True)
        self.pack_end(self.back, False, True)
        
        self.logger.connect('clicked', self.on_logger_clicked, None)
        self.theme.connect('clicked', self.on_theme_clicked, None)
        self.help.connect('clicked', self.on_help_clicked, None)
        self.back.connect('clicked', self.on_back_clicked, None)
        self.next.connect('clicked', self.on_next_clicked, None)
    
    def img_label_box(self, img_path, label_text):
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(0)
        img = gtk.Image()
        img.set_from_file(img_path)
        label = gtk.Label(label_text)
        hbox.pack_start(img, False, False, 2)
        hbox.pack_start(label, False, False, 2)
        img.show()
        label.show()
        return hbox
        
    def on_logger_clicked(self, widget, data):
        pass
    def on_theme_clicked(self, widget, data):
        pass
    def on_help_clicked(self, widget, data):
        pass
    def on_back_clicked(self, widget, data):
        self.sself.btnback_clicked(self, data)
    def on_next_clicked(self, widget, data):
        self.sself.btnnext_clicked(self, data)
