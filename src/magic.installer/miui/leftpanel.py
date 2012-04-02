#!/usr/bin/python
import gtk
from miutils.milogger import ClientLogger
log = ClientLogger.get_instance(ClientLogger, __name__)

class StepButton(gtk.Button):
    def __init__(self, img_path, label_text, *args, **kw):
        gtk.Button.__init__(self, *args, **kw)
        self.img = None
        self.label = None
        self.box = self.img_label_box(img_path, label_text)
        self.add(self.box)
        
    def img_label_box(self, img_path, label_text):
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(0)
        self.img = gtk.Image()
        self.img.set_from_file(img_path)
        self.label = gtk.Label(label_text)
        hbox.pack_start(self.img, False, False, 2)
        hbox.pack_start(self.label, False, False, 2)
        self.img.show()
        self.label.show()
        return hbox
        
    def change_image(self, img_path):
        self.img.set_from_file(img_path)
        
class MILeftPanel(gtk.Frame):
    def __init__(self, sself, *args, **kw):
        gtk.Frame.__init__(self, *args, **kw)
        self.sself = sself
        self.vbox = gtk.VBox()
        self.btn_lst = []
        
        self.vbox.set_border_width(4)
        self.vbox.set_spacing(4)
        self.vbox.show()
        self.add(self.vbox)
        
    def addstep(self, name):
        log.d('addstep %s' % name)
        step = self.sself.steps.get_step_by_name(name)

        btn = StepButton('images/applet-blank.png', step.title)
        btn.connect('clicked', self.on_switch_to_page, name)

        self.btn_lst.append(btn)
        self.vbox.pack_start(btn, False, False)
        
    def skip_step(self, name):
        s_id = self.sself.steps.get_id_by_name(name)
        self.btn_lst[s_id].set_sensitive(False)
    
    def on_switch_to_page(self, widget, name):
        self.sself.switch_to_page(name)
        
    def switch(self, from_id, to_id):
        self.btn_lst[from_id].change_image('images/applet-blank.png')
        self.btn_lst[to_id].change_image('images/applet-busy.png')