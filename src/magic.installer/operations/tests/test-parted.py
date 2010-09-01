#!/usr/bin/python
# Copyright (C) 2003, Charles Wang <charles@linux.net.cn>
# Author:  Charles Wang

import parted

operation_type = 'long'

execfile('../parted.py')

class miaclass:
    def set_step(self, operid, step, stepnum):
        pass

mia = miaclass()

print device_probe_all(mia, 1, -1)
