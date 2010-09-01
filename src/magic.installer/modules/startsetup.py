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

class mistep_startsetup (magicstep.magicstep):
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'startsetup.xml', 'startsetup')

    def get_label(self):
        return _("Start to setup")
        
    def btnnext_clicked(self, widget, data):
        # We add a skip step name to current class, 
        # and it will remove the step in magic.installer class
        self.fetch_values(self.rootobj.values,
                valuename_list = ['startsetup.skipXsetting'])
        skipXsetting = self.get_data(self.values, 'startsetup.skipXsetting')
        if skipXsetting == '1':
            self.skip_stepnames.append('mistep_Xwindow')
        return  1
