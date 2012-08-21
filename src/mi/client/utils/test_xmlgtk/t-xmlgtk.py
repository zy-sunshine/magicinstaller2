#!/usr/bin/python
# Copyright (C) 2003, Charles Wang
# Author: Charles Wang <charles@linux.net.cn>
import gtk
import sys
from xml.dom.minidom import parse

from mi.client.utils import xmlgtk

xml_data = parse('t-xmlgtk-data.xml')

class t_xmlgtk(xmlgtk.xmlgtk):
    def __init__(self, uixmldoc, uixml_rootname=None):
        xmlgtk.xmlgtk.__init__(self, uixmldoc, uixml_rootname)
        #selection = self.name_map['testlist_treeview'].get_selection()
        #selection.set_select_function(self.echo_show, 'data')

    def fetch_values_clicked(self, widget, data):
        global xml_data
        self.fetch_values(xml_data)
        print xml_data.toxml()

    def show_selection(self, widget, data):
        print '================='
        selection = self.name_map['testlist_treeview'].get_selection()
        selection.selected_foreach(self.each_show, 'data')
        print '================='

    def each_show(self, model, path, iter, data):
        #print [self, model, path, iter, data]
        print [model.get_value(iter, 0),
               model.get_value(iter, 1)]

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.set_border_width(4)
window.set_position(gtk.WIN_POS_CENTER)

xml_interface = parse('t-xmlgtk.xml')

xgobj = t_xmlgtk(xml_interface)
xgobj.fill_values(xml_data.documentElement)

window.add(xgobj.widget)
window.show_all()

gtk.main()
