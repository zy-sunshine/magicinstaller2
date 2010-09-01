#!/usr/bin/python
# Copyright (C) 2003, Charles Wang <charles@linux.net.cn>
# Author:  Charles Wang.

import parted

print '*** file_system_type ***'
fstype = parted.file_system_type_get_next()
while fstype:
    print fstype.name
    fstype = parted.file_system_type_get_next(fstype)
print

print '*** disk_type ***'
disktype = parted.disk_type_get_next()
while disktype:
    print disktype.name
    disktype = parted.disk_type_get_next(disktype)
