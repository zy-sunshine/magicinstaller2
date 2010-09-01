#!/usr/bin/python

import os
import sys
import time
import miactions

mia = miactions.MIActions(4, 1024, 32)

if mia.pid > 0:
    while 1:
        rlist = mia.get_result()
        if rlist != []:
            print rlist
        (is_alive, exit_val) = mia.action_alive()
        if not is_alive:
            print 'exit_val =', exit_val
            break
        miactions.usleep(100)
elif mia.pid == 0:
    for str in ['yes', 'no', 'right', 'ok']:
        #print str
        mia.put_result(str)

