#!/usr/bin/python
# Copyright (C) 2003, Charles Wang.
# Author: Charles Wang <charles@linux.net.cn>
import sys
if len(sys.argv) != 3:
    print "Usage: python t-xmlgtk-show.py uixmldoc rootname"
    sys.exit(1)
sys.path.insert(0, '.')
import gtk
from xml.dom.minidom import parse
import xmlgtk

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

xml_interface = parse(sys.argv[1])
xgobj = dummy_xmlgtk(xml_interface, sys.argv[2])

window.add(xgobj.widget)
window.show_all()

gtk.main()
