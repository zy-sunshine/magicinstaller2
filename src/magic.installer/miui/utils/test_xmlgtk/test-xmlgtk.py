#!/usr/bin/python
# Copyright (C) 2003, Charles Wang <charles@linux.net.cn>
# Author:  Charles Wang.
import gtk
import sys
from xml.dom.minidom import parse

from miui.utils import xmlgtk

def write_xml(*args):
    global xgobj
    xgobj.fetch_values(xml_data)
    f = file('test-xmlgtk-data.result.xml', 'w')
    xml_data.writexml(f)
    f.close()
    gtk.main_quit()

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.connect("destroy", write_xml)
window.set_border_width(10)
window.set_position(gtk.WIN_POS_CENTER)

xml_interface = parse('test-xmlgtk.xml')
xml_data = parse('test-xmlgtk-data.xml')

add_count = 0

class test_xmlgtk_pop (xmlgtk.xmlgtk):
    def __del__(self):
        global xml_data
        self.fetch_values(xml_data)

    def show_changed(self, treesel, data):
        iter = treesel.get_selected()
        print iter
        if iter[1]:
            print iter[0].get_value(iter[1], 0), \
                  iter[0].get_value(iter[1], 1), \
                  iter[0].get_value(iter[1], 2)

    def add_clicked(self, button, data):
        global add_count
        print 'add_clicked'
        newrow = self.uixmldoc.createElement('row')
        newrow.setAttribute('c0', 'no.png')
        newrow.setAttribute('c1', 'OK(%d)' % add_count)
        newrow.setAttribute('c2', 'KO(%d)' % add_count)
        self.list_insert('list', 5, newrow)
        add_count = add_count + 1

    def add_before_clicked(self, button, data):
        global add_count
        print 'add_before_clicked'
        newrow = self.uixmldoc.createElement('row')
        newrow.setAttribute('c0', 'no.png')
        newrow.setAttribute('c1', 'OK(%d)' % add_count)
        newrow.setAttribute('c2', 'KO(%d)' % add_count)
        iter = self.name_map['TestList_treeview'].get_selection().get_selected()
        if iter:
            self.list_insert_before('list', iter[1], newrow)
        add_count = add_count + 1

    def add_after_clicked(self, button, data):
        global add_count
        print 'add_after_clicked'
        newrow = self.uixmldoc.createElement('row')
        newrow.setAttribute('c0', 'no.png')
        newrow.setAttribute('c1', 'OK(%d)' % add_count)
        newrow.setAttribute('c2', 'KO(%d)' % add_count)
        iter = self.name_map['TestList_treeview'].get_selection().get_selected()
        if iter:
            self.list_insert_after('list', iter[1], newrow)
        add_count = add_count + 1

    def replace_clicked(self, button, data):
        global add_count
        print 'replace_clicked'
        newrow = self.uixmldoc.createElement('row')
        newrow.setAttribute('c0', 'no.png')
        newrow.setAttribute('c1', 'OK(%d)' % add_count)
        newrow.setAttribute('c2', 'KO(%d)' % add_count)
        iter = self.name_map['TestList_treeview'].get_selection().get_selected()
        if iter:
            self.list_replace('list', iter[1], newrow)
        add_count = add_count + 1

    def remove_clicked(self, button, data):
        print 'remove_clicked'
        iter = self.name_map['TestList_treeview'].get_selection().get_selected()
        if iter:
            self.list_remove('list', iter[1])


class test_xmlgtk (xmlgtk.xmlgtk):
    def test_clicked(self, button, data):
        print "It is clicked."
        top = gtk.Window(gtk.WINDOW_TOPLEVEL)
        pop_interface = parse('test-xmlgtk-pop.xml')
        xgobj = test_xmlgtk_pop(pop_interface)
        xgobj.fill_values(xml_data.documentElement)
        top.add(xgobj.widget)
        top.show_all()

    def test_toggled(self, button, data):
        print "It is toggled."

xgobj = test_xmlgtk(xml_interface)

xgobj.fill_values(xml_data.documentElement)

window.add(xgobj.widget)

window.show_all()

gtk.main()
