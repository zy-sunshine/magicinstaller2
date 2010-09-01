#!/usr/bin/python
# Copyright (C) 2003, Charles Wang <charles@linux.net.cn>
# Author:  Charles Wang
import gtk
import sys
from xml.dom.minidom import parse

sys.path.insert(0, '..')

import xmlgtk

def progquit(widget):
    gtk.main_quit()

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.connect('destroy', progquit)

stxml = parse('showtheme.xml')

st = xmlgtk.xmlgtk(stxml)

window.add(st.widget)

window.show_all()

gtk.main()
