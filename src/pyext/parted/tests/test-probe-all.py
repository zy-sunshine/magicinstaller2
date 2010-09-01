#!/usr/bin/python
# Copyright (C) 2003, Charles Wang <charles@linux.net.cn>
# Author:  Charles Wang.

import parted

print 'AAA'

# device_probe_all might be a long operation, it take 5 minutes in
# my computer.
parted.device_probe_all()
print 'BBB'

devlist = parted.device_get_all()
print devlist
print 'CCC'

for dev in devlist:
    print dev.model, dev.path, dev.length
    disk = parted.PedDisk.new(dev)
    print disk
