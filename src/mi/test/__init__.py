import gtk
from xml.dom.minidom import parse
from mi.utils.common import search_file
from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()
class FakeTaskManager():
    def add_action(self, *args, **kw):
        pass
    
class TestMIStep(gtk.Window):
    def __init__(self, *args, **kw):
        gtk.Window.__init__(self, *args, **kw)
        self.values = parse(search_file('magic.values.xml', [CF.D.HOTFIXDIR, '.']))
        self.connect('destroy', lambda x: gtk.main_quit())
        self.tm = FakeTaskManager()
        
    def add_mistep(self, mistep):
        #### TODO: left panel and right panel in takeactions
        self.hbox = gtk.HBox()
        self.hbox.pack_start(mistep.widget, True, True)
        if hasattr(mistep, 'get_left_panel'):
            self.hbox.pack_start(mistep.get_left_panel(), True, True)
        if hasattr(mistep, 'get_right_panel'):
            self.hbox.pack_start(mistep.get_right_panel(), True, True)
            
        self.add(self.hbox)
        