#!/usr/bin/python
import gtk
from mi.client.utils import _

class MIButtonBar(gtk.HBox):
    def __init__(self, sself, *args, **kw):
        gtk.HBox.__init__(self, *args, **kw)
        self.sself = sself
        
        self.logger = gtk.Button()
        self.theme = gtk.Button( _('_Theme'))
        self.help = gtk.Button()
        self.back = gtk.Button()
        self.next = gtk.Button()
        self.cancel = gtk.Button()
        self.finish = gtk.Button()
            
        self.logger.add(self.img_label_box('images/stock_help_24.png', _('_Logger')))
        #self.theme.add(self.img_label_box('images/gnome-ccthemes-24.png', _('_Theme')))
        self.help.add(self.img_label_box('images/stock_help_24.png', _('_Help')))
        self.back.add(self.img_label_box('images/stock_left_arrow_24.png', _('_Back')))
        self.next.add(self.img_label_box('images/stock_right_arrow_24.png', _('_Next')))
        
        self.cancel.add(self.img_label_box('images/stock_exit_24.png', _('_Cancel')))
        self.finish.add(self.img_label_box('images/stock_exit_24.png', _('_Finish')))

        self.set_border_width(4)
        self.set_spacing(4)
        #self.pack_start(self.logger, False, True)
        self.pack_start(self.theme, False, True)
        self.pack_start(self.help, False, True)
        
        self.pack_end(self.cancel, False, True)
        self.pack_end(self.next, False, True)
        self.pack_end(self.back, False, True)
        self.pack_end(self.finish, False, True)
        
        self.logger.connect('clicked', self.logger_btn_clicked, None)
        self.theme.connect('clicked', self.theme_btn_clicked, None)
        self.help.connect('clicked', self.help_btn_clicked, None)
        self.back.connect('clicked', self.back_btn_clicked, None)
        self.next.connect('clicked', self.next_btn_clicked, None)
        
        self.cancel.connect('clicked', self.sself.btncancel_clicked, None)
        self.finish.connect('clicked', self.sself.btnfinish_clicked, None)
        
    def img_label_box(self, img_path, label_text):
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(0)
        img = gtk.Image()
        img.set_from_file(img_path)
        label = gtk.Label(label_text)
        label.set_use_underline(True)
        hbox.pack_start(img, False, False, 2)
        hbox.pack_start(label, False, False, 2)
        img.show()
        label.show()
        return hbox
        
    def logger_btn_clicked(self, widget, data):
        self.sself.btnlogger_clicked(widget, data)
    
    def theme_btn_clicked(self, widget, data):
        self.sself.btntheme_clicked(widget, data)
        
    def help_btn_clicked(self, widget, data):
        self.sself.btnhelp_clicked(widget, data)
    
    def back_btn_clicked(self, widget, data):
        self.sself.btnback_clicked(self, data)
        
    def next_btn_clicked(self, widget, data):
        self.sself.btnnext_clicked(self, data)

    def switch(self, newstep):
        if(hasattr(newstep, 'btnfinish_clicked')):
            self.finish.show()
        else:
            self.finish.hide()
            
        if(hasattr(newstep, 'btncancel_clicked')):
            self.cancel.show()
        else:
            self.cancel.hide()
