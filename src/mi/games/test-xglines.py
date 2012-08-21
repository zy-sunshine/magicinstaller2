#!/usr/bin/python
# Copyright (C) 2003, Charles Wang <charles@linux.net.cn>
# Author:  Charles Wang.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANT; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public LIcense for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.

import gtk
import sys

sys.path.insert(0, '..')

import xmlgtk
import xglines

def exit_game():
    gtk.main_quit()

topwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
topwin.connect('destroy', exit_game)
topwin.set_position(gtk.WIN_POS_CENTER)

xgobj = xglines.xglines('', None, exit_game)

topwin.add(xgobj.widget)
topwin.show_all()

gtk.main()
