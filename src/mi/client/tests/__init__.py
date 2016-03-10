#!/usr/bin/python
from xml.dom.minidom import parse
from mi.utils.common import search_file
import gtk

class MiTaskman_Fake(object):
    def add_action(self, *args, **kw):
        pass
    
    def push_progress(self, *args, **kw):
        pass
    
class TestRootObject(object):
    def __init__(self, xmlgtk_class):
        self.tm = MiTaskman_Fake()
        self.values = parse(search_file('magic.values.xml', ['.']))
        self.xmlgtk_class = xmlgtk_class
        
    def init(self):
        self.xmlgtk_obj = self.xmlgtk_class(self)
        
    def main(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_border_width(4)
        window.set_size_request(800, 600)
        window.set_position(gtk.WIN_POS_CENTER)
        window.add(self.xmlgtk_obj.widget)
        window.connect('destroy', lambda x: gtk.main_quit())
        window.show()
        gtk.main()
        