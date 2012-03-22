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

import part
import abspart

pm = abspart.PartitionManager()

for hd in pm.harddisks:
    if hd.valid:
        sp = hd.get_space_list()
        for ap in sp:
            print '%d(0x%x): %d - %d' % (ap.part_number, ap.part_type,
                                         ap.start_cylinder, ap.end_cylinder)
    else:
        str = ''
        for err in hd.PErrArr:
            str = str + ' ' + part.strPErr(err)
        print 'INVALID:' + str
