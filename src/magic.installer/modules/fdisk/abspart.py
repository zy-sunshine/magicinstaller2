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

import glob
import os
import os.path
import string

import lowlevel

import part

class AbstructPartition :
    def __init__(self, orig=None):
        # part_type:  EMPTY means a blank cell in harddisk.
        self.part_type = part.EMPTY
        self.start_cylinder = 0 # start_xxx specify the start of the partition.
        self.start_head = 0
        self.end_cylinder = 0 # end_xxx specify the end of the partition.
        # orig_start_cylinder: The original start cylinder of the partition.
        #   If it is -1, the partition is a new allocated partition.
        self.orig_start_cylinder = -1
        self.part_number = 0  # The partition number.
        # orig_part_number: The original partition number.
        #   If it is -1, the partition is a new allocated partition.
        self.orig_part_number = -1
        self.mount_pointer = ''
        self.filesystem = ''
        self.format_or_not = 0
        if orig:
            self.part_type = orig.part_type
            self.start_cylinder = orig.start_cylinder
            self.orig_start_cylinder = orig.start_cylinder
            self.start_head = orig.start_head
            self.end_cylinder = orig.end_cylinder
            self.part_number = orig.partnum
            self.orig_part_number = orig.partnum

class AbstructDevicePartitions:
    def __init__(self, devpath):
        self.valid = 1
        self.PErrArr = []
        self.devpath = devpath
        devfn = os.path.basename(devpath)
        if devfn[:2] == 'hd':
            self._mknod_ide(devpath)
        elif devfn[:2] == 'sd':
            self._mknod_scsi(devpath)
        else:
            self.valid = 0
            self.PErrArr.append(part.PErr_Unknown_HDType)
            return
        self.origdp = part.devparts(devpath)
        if not self.origdp.valid:
            self.valid = 0
            self.PErrArr = self.PErrArr + self.origdp.PErrArr
            return
        self.absparts = []
        self.load_abspart()

    def load_abspart(self):
        self.absparts = []
        for prim in self.origdp.prim:
            if prim.part_type == part.EXTENDED:
                for logic in self.origdp.logics:
                    self.absparts.append(AbstructPartition(logic))
            elif prim.part_type != part.EMPTY:
                self.absparts.append(AbstructPartition(prim))

    def add_part(self, start_cylinder, end_cylinder):
        pass

    def move_part(self, start_cylinder, end_cylinder, start_cylinder_to):
        pass

    def remove_part(self, start_cylinder):
        index = 0
        while index < len(self.absparts):
            ap = self.absparts[index]
            if ap.start == start_cylinder:
                del self.absparts[index]
                return 1
            index = index + 1
        return 0 # Can't find the partition to delete.

    def get_space_list(self):
        result = []
        cur_start = 0
        for ap in self.absparts:
            if ap.start_cylinder > cur_start:
                empty_ap = AbstructPartition()
                empty_ap.start_cylinder = cur_start
                empty_ap.end_cylinder = ap.start_cylinder - 1
                result.append(empty_ap)
            result.append(ap)
            cur_start = ap.end_cylinder + 1
        if cur_start < self.origdp.cylinders():
            empty_ap = AbstructPartition()
            empty_ap.start_cylinder = cur_start
            empty_ap.end_cylinder = self.origdp.cylinders() - 1
            result.append(empty_ap)
        return result

    def _mknod_ide(self, devpath):
        ide_rdev = [lowlevel.makedev( 3,  0), lowlevel.makedev( 3, 64),
                    lowlevel.makedev(22,  0), lowlevel.makedev(22, 64),
                    lowlevel.makedev(33,  0), lowlevel.makedev(33, 64),
                    lowlevel.makedev(34,  0), lowlevel.makedev(34, 64),
                    lowlevel.makedev(56,  0), lowlevel.makedev(56, 64),
                    lowlevel.makedev(57,  0), lowlevel.makedev(57, 64),
                    lowlevel.makedev(88,  0), lowlevel.makedev(88, 64),
                    lowlevel.makedev(89,  0), lowlevel.makedev(89, 64),
                    lowlevel.makedev(90,  0), lowlevel.makedev(90, 64),
                    lowlevel.makedev(91,  0), lowlevel.makedev(91, 64)]
        devfn = os.path.basename(devpath)
        dev_t0 = ide_rdev[ord(devfn[2]) - ord('a')]
        if devfn[3:] == '':
            dev_t1 = 0
        else:
            dev_t1 = int(devfn[3:])
        lowlevel.mknod(devpath, 0600 | lowlevel.S_IFBLK, dev_t0 + dev_t1)

    def _mknod_scsi(self, devpath):
        scsi_rdev = [lowlevel.makedev( 8,   0), lowlevel.makedev( 8,  16),
                     lowlevel.makedev( 8,  32), lowlevel.makedev( 8,  48),
                     lowlevel.makedev( 8,  64), lowlevel.makedev( 8,  80),
                     lowlevel.makedev( 8,  96), lowlevel.makedev( 8, 112),
                     lowlevel.makedev( 8, 128), lowlevel.makedev( 8, 144),
                     lowlevel.makedev( 8, 160), lowlevel.makedev( 8, 176),
                     lowlevel.makedev( 8, 192), lowlevel.makedev( 8, 208),
                     lowlevel.makedev( 8, 224), lowlevel.makedev( 8, 240),
                     lowlevel.makedev(65,   0), lowlevel.makedev(65,  16),
                     lowlevel.makedev(65,  32), lowlevel.makedev(65,  48),
                     lowlevel.makedev(65,  64), lowlevel.makedev(65,  80),
                     lowlevel.makedev(65,  96), lowlevel.makedev(65, 112),
                     lowlevel.makedev(65, 128), lowlevel.makedev(65, 144)]
        devfn = os.path.basename(devpath)
        dev_t0 = scsi_rdev[ord(devfn[2]) - ord('a')]
        if devfn[3:] == '':
            dev_t1 = 0
        else:
            dev_t1 = int(devfn[3:])
        lowlevel.mknod(devpath, 0600 | lowlevel.S_IFBLK, dev_t0 + dev_t1)

class PartitionManager:
    def __init__(self):
        # harddisks contain all harddisks.
        self.harddisks = []
        self.scan_all_idedisks()
        self.scan_all_scsidisks()

    def scan_all_idedisks(self):
        for idedisk in glob.glob('/proc/ide/hd*'):
            content = self.readfile(idedisk + '/media')
            if content == 'disk\n':
                disk = os.path.basename(idedisk)
                self.harddisks.append(AbstructDevicePartitions('/tmp/dev/' + disk))

    def scan_all_scsidisks(self):
        pass

    def readfile(self, filename):
        f = file(filename, 'r')
        content = f.read()
        f.close()
        return content
