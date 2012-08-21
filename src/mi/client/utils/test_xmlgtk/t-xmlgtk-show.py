#!/usr/bin/python
# Copyright (C) 2003, Charles Wang.
# Author: Charles Wang <charles@linux.net.cn>
import sys
import gtk
from xml.dom.minidom import parse
from mi.client.utils import xmlgtk

if len(sys.argv) not in (2, 3):
    print "Usage: python t-xmlgtk-show.py uixmldoc [rootname]"
    sys.exit(1)

uixmldoc = sys.argv[1]
if len(sys.argv) == 3:
    rootname = sys.argv[2];
else:
    rootname = None

class dummy_xmlgtk(xmlgtk.xmlgtk):
    def __init__(self, uixmldoc, uixml_rootname=None):
        xmlgtk.xmlgtk.__init__(self, uixmldoc, uixml_rootname)

    def __getattr__(self, name):
        return self.dummy

    def dummy(self, widget, data=None):
        pass

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.connect('destroy', gtk.main_quit)
window.set_border_width(4)
window.set_position(gtk.WIN_POS_CENTER)
window.set_size_request(600, 600)
window.set_resizable(True)

xgobj = dummy_xmlgtk(parse(uixmldoc), rootname)
window.add(xgobj.widget)

window.show_all()
gtk.main()
