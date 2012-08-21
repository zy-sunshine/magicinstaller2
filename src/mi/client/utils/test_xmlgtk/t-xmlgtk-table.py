#!/usr/bin/python
# Copyright (C) 2003, Charles Wang.
# Author: Charles Wang <charles@linux.net.cn>
import gtk
import sys
from xml.dom.minidom import parse

from mi.client.utils import xmlgtk

class t_xmlgtk_table(xmlgtk.xmlgtk):
    def __init__(self, uixmldoc, uixml_rootname=None):
        xmlgtk.xmlgtk.__init__(self, uixmldoc, uixml_rootname)

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.set_border_width(4)
window.set_position(gtk.WIN_POS_CENTER)

xml_interface = parse('t-xmlgtk-table.xml')

xgobj = t_xmlgtk_table(xml_interface)

window.add(xgobj.widget)
window.show_all()

gtk.main()

