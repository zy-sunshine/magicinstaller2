#!/usr/bin/python
# Copyright (C) 2003, Charles Wang.
# Author:  Charles Wang <charles@linux.net.cn>
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

class mistep_testops (magicstep.magicstep):
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'testops.xml')

    def get_label(self):
        return  _("Test")

    def btnback_clicked(self, widget, data):
        return  1

    def btnnext_clicked(self, widget, data):
        return  1

    def startsleep(self, widget, data):
        self.name_map['sleepbtn'].set_sensitive(False)
        self.rootobj.tm.add_action('Test Op: Sleep', self.stopsleep, None, 'sleep', 5)

    def stopsleep(self, operid, data):
        self.name_map['sleepbtn'].set_sensitive(True)
