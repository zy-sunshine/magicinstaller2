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

import os
from gettext import gettext as _

import extioctl

EMPTY           = 0x00
FAT12           = 0x01
EXTENDED        = 0x05
FAT16           = 0x06
WIN95_FAT32     = 0x0b
WIN95_FAT32_LBA = 0x0c
WIN95_FAT16_LBA = 0x0e
WIN95_EXT       = 0x0f
LINUX_SWAP      = 0x82
LINUX           = 0x83

PErr_Invalid_Active    = 1
PErr_Invalid_Start     = 2
PErr_Invalid_End       = 3
PErr_Invalid_Size      = 4
PErr_Multi_Prim_Ext    = 5
PErr_Multi_Logic_InExt = 6
PErr_Multi_Ext_InExt   = 7
PErr_Wrong_Part_Seq    = 8
PErr_Unknown_HDType    = 9

def strPErr(PErrNo):
    if PErrNo == PErr_Invalid_Active:
        return _('Active item is not 0x0 and 0x80.')
    elif PErrNo == PErr_Invalid_Start:
        return _('Partition is start from an invalid sector.')
    elif PErrNo == PErr_Invalid_End:
        return _('Partition is end at an invalid sector.')
    elif PErrNo == PErr_Invalid_Size:
        return _('The size of partition can be negative.')
    elif PErrNo == PErr_Multi_Prim_Ext:
        return _('There are more than one extended partitions in primary partition table.')
    elif PErrNo == PErr_Multi_Logic_InExt:
        return _('More than one logic partitions present in a single extended partition table.')
    elif PErrNo == PErr_Multi_Ext_InExt:
        return _('More then one extended partitions present in a single extended partition table.')
    elif PErrNo == PErr_Wrong_Part_Seq:
        return _('Wrong partition sequence.')
    elif PErrNo == PErr_Unknown_HDType:
        return _('Unknown harddisk type.')
    else:
        return _('Unknown PErr code %d.') % PErrNo

class part:
    def __init__(self, geo_head, geo_sector, ptsec, partnum, partbytes):
        self.valid = 1
        self.PErrArr = []
        if ord(partbytes[0]) == 0x0:
            self.active = 0
        elif ord(partbytes[0]) == 0x80:
            self.active = 1
        else:
            self.PErrArr.append(PErr_Invalid_Active)
            self.valid = 0
        self.partnum = partnum
        self.start_cylinder = ord(partbytes[3]) | ((ord(partbytes[2]) & 0xc0) << 2)
        self.start_head = ord(partbytes[1])
        self.start_sector = ord(partbytes[2]) & 0x3f
        self.part_type = ord(partbytes[4])
        self.end_cylinder = ord(partbytes[7]) | ((ord(partbytes[6]) & 0xc0) << 2)
        self.end_head = ord(partbytes[5])
        self.end_sector = ord(partbytes[6]) & 0x3f
        self.start4 = self.read4_little_endian(partbytes[8:12])
        self.size4 = self.read4_little_endian(partbytes[12:16])
        self.startsec = ptsec + self.start4
        self.endsec = self.startsec + self.size4 - 1
        if self.startsec >= 1024 * geo_head * geo_sector:
            self.start_cylinder = self.startsec / (geo_head * geo_sector)
            self.start_head = (self.startsec / geo_sector) % geo_head
            self.start_sector = self.startsec % geo_sector + 1
        if self.endsec >= 1024 * geo_head * geo_sector:
            self.end_cylinder = self.endsec / (geo_head * geo_sector)
            self.end_head = (self.endsec / geo_sector) % geo_head
            self.end_sector = self.endsec % geo_sector + 1
        if self.part_type != EMPTY:
            if (self.start_head != 0 and self.start_head != 1) or self.start_sector != 1:
                self.valid = 0
                self.PErrArr.append(PErr_Invalid_Start)
            if self.end_head + 1 != geo_head and self.end_sector != geo_sector:
                self.valid = 0
                self.PErrArr.append(PErr_Invalid_End)
            if self.start_cylinder > self.end_cylinder:
                self.valid = 0
                self.PErrArr.append(PErr_Invalid_Size)

    def write2bytes(self, partbytes):
        if self.valid:
            if self.active:
                partbytes[0] = 0x80
            else:
                partbytes[0] = 0x0
            if self.start_cylinder < 1024:
                partbytes[1] = chr(self.start_head)
                partbytes[2] = chr(self.start_sector | ((self.start_cylinder & 0x300) >> 2))
                partbytes[3] = chr(self.start_cylinder & 0xff)
            else:
                partbytes[1] = chr(geo_head - 1)
                partbytes[2] = chr(geo_sector | 0xc0)
                partbytes[3] = 0xff
            partbytes[4] = chr(self.part_type)
            if self.end_cylinder < 1024:
                partbytes[5] = chr(self.end_head)
                partbytes[6] = chr(self.end_sector | ((self.end_cylinder & 0x300) >> 2))
                partbytes[7] = chr(self.end_cylinder & 0xff)
            else:
                partbytes[5] = chr(geo_head - 1)
                partbytes[6] = chr(geo_sector | 0xc0)
                partbytes[7] = 0xff
            self.write4_little_endian(self.start4, partbytes[8:12])
            self.write4_little_endian(self.size4, partbytes[12:16])

    def read4_little_endian(self, bytes):
        return ord(bytes[0]) + (ord(bytes[1]) << 8) + (ord(bytes[2]) << 16) + (ord(bytes[3]) << 24)

    def write4_little_endian(self, value, bytes):
        bytes[0] = chr(value & 0xff)
        bytes[1] = chr((value >> 8) & 0xff)
        bytes[2] = chr((value >> 16) & 0xff)
        bytes[3] = chr((value >> 24) & 0xff)

    def __str__(self):
        s = ''
        if not self.valid:
            s = 'INVALID:' + str(self.PErrArr)
            return s
        s = s + ('%d: ' % self.partnum)
        if self.active:
            s = s + 'A'
        s = s + '(%d,%d,%d) - (%d,%d,%d) Type=%d, Start4=%d, Size=%d' % \
            (self.start_cylinder, self.start_head, self.start_sector,
             self.end_cylinder, self.end_head, self.end_sector,
             self.part_type, self.start4, self.size4)
        return s

class devparts:
    def __init__(self, devfn):
        self.valid = 1
        self.PErrArr = []
        self.devpath = devfn
        self.geo = extioctl.HDIO_GETGEO(devfn)
        devfd = os.open(devfn, os.O_RDONLY)
        # Get the geometry of the device.
        # Read the primary partition table in.
        buffer = os.read(devfd, 512)
        self.prim = []
        self.prim.append(self._cpart(0, 1, buffer[0x1be:0x1ce]))
        self.prim.append(self._cpart(0, 2, buffer[0x1ce:0x1de]))
        self.prim.append(self._cpart(0, 3, buffer[0x1de:0x1ee]))
        self.prim.append(self._cpart(0, 4, buffer[0x1ee:0x1fe]))
        self.prim_orig_buffer = buffer
        # Initial for read the logic partition table in.
        self.logics = []
        self.logic_orig_buffers = []
        primext_offset = 0
        cur_offset = -1
        for p in self.prim:
            if not p.valid:
                self.valid = 0
                self.PErrArr = self.PErrArr + p.PErrArr
                continue
            if p.part_type == EXTENDED:
                primext_offset = p.start4
                cur_offset = p.start4
                break
        logicnum = 5
        while cur_offset > 0:
            os.lseek(devfd, 512 * cur_offset, 0)
            buffer = os.read(devfd, 512)
            parts = []
            parts.append(self._cpart(cur_offset, logicnum, buffer[0x1be:0x1ce]))
            parts.append(self._cpart(cur_offset, logicnum, buffer[0x1ce:0x1de]))
            parts.append(self._cpart(cur_offset, logicnum, buffer[0x1de:0x1ee]))
            parts.append(self._cpart(cur_offset, logicnum, buffer[0x1ee:0x1fe]))
            blank_count = 0
            logic_count = 0
            extend_count = 0
            for p in parts:
                if not p.valid:
                    self.valid = 0
                    continue
                if p.part_type == EXTENDED:
                    next_offset = primext_offset + p.start4
                    extend_count = extend_count + 1
                elif p.part_type != EMPTY:
                    self.logics.append(p)
                    self.logic_orig_buffers.append(buffer)
                    logic_count = logic_count + 1
                else:
                    blank_count = blank_count + 1
            if logic_count == 1 and extend_count == 1 and blank_count == 2:
                cur_offset = next_offset
            elif logic_count == 1 and extend_count == 0 and blank_count == 3:
                break
            else:
                self.valid = 0
                if logic_count > 1:
                    self.PErrArr.append(PErr_Multi_Logic_InExt)
                if extend_count > 1:
                    self.PErrArr.append(PErr_Multi_Ext_InExt)
                break
            logicnum = logicnum + 1
        os.close(devfd)
        # Check validation
        if self.valid:
            extend_count = 0
            for prim in self.prim:
                if prim.part_type == EXTENDED:
                    extend_count = extend_count + 1
            if extend_count > 1:
                self.valid = 0
                self.PErrArr.append(PErr_Multi_Prim_Ext)
        if self.valid:
            min_start = 0
            for prim in self.prim:
                if not self.valid:
                    break
                if prim.part_type == EMPTY:
                    continue
                if min_start > prim.start_cylinder:
                    self.valid = 0
                    self.PErrArr.append(PErr_Wrong_Part_Seq)
                    break
                if prim.part_type == EXTENDED:
                    for logic in self.logics:
                        if min_start > logic.start_cylinder:
                            self.valid = 0
                            self.PErrArr.append(PErr_Wrong_Part_Seq)
                            break
                        min_start = logic.end_cylinder + 1
                elif prim.part_type != EMPTY:
                    min_start = prim.end_cylinder + 1

    def cylinders(self):
        return  self.geo['cylinders']

    def heads(self):
        return  self.geo['heads']

    def sectors(self):
        return  self.geo['sectors']

    def __str__(self):
        s = ''
        for p in self.prim:
            s = s + str(p) + '\n'
        for p in self.logics:
            s = s + str(p) + '\n'
        return s

    def _cpart(self, ptsec, partnum, partbytes):
        return  part(self.geo['heads'], self.geo['sectors'], ptsec, partnum, partbytes)
