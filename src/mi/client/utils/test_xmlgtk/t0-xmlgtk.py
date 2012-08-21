#!/usr/bin/python
# Copyright (C) 2003, Charles Wang
# Author: Charles Wang <charles@linux.net.cn>
import gtk
import sys
from xml.dom.minidom import parse

from mi.client.utils import xmlgtk

class t0_xmlgtk(xmlgtk.xmlgtk):
    def __init__(self, uixmldoc, uixml_rootname=None):
        xmlgtk.xmlgtk.__init__(self, uixmldoc, uixml_rootname)
        self.name_map['btn1'].connect('enter-notify-event',
                                      self.show_text,
                                      'DESC BTN1 (AAA)')
        self.name_map['btn1'].connect('leave-notify-event',
                                      self.show_text, '')
        self.name_map['btn2'].connect('enter-notify-event',
                                      self.show_text,
                                      'DESC BTN2 (BBB)')
        self.name_map['btn2'].connect('leave-notify-event',
                                      self.show_text, '')
    def show_text(self, widget, event, data):
        self.name_map['btndesc'].set_text(data)

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.set_border_width(4)
window.set_position(gtk.WIN_POS_CENTER)

xml_interface = parse('t0-xmlgtk.xml')

xgobj = t0_xmlgtk(xml_interface)

window.add(xgobj.widget)
window.show_all()

gtk.main()
