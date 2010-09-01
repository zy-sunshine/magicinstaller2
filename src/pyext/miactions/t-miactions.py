#!/usr/bin/python

import os
import sys
import miactions

mia = miactions.MIActions(4, 1024, 32)

if mia.pid > 0:
    # Control process.
    orig_id = 0
    orig_step = 0
    orig_stepnum = 0
    print "Control process: %d" % os.getpid()
    print "CP:", mia.put_operation('THE FIRST OPERATION')
    print "CP:", mia.put_operation('THE SECOND OPERATION')
    print "CP:", mia.put_operation('THE THIRD OPERATION')
    print "CP:", mia.put_operation('quit')
    while 1:
        (id, step, stepnum) = mia.probe_step()
        if id != orig_id or step != orig_step or stepnum != orig_stepnum:
            print 'probe_step:', (id, step, stepnum)
            orig_id = id
            orig_step = step
            orig_stepnum = stepnum
        result_list = mia.get_result()
        if result_list != []:
            print result_list
        (is_alive, exit_val) = mia.action_alive()
        if not is_alive:
            print 'exit_val =', exit_val
            break
        miactions.usleep(100)
elif mia.pid == 0:
    # Action process.
    print "Action process: %d" % os.getpid()
    while 1:
        (id, opera) = mia.get_operation()
        print 'id = %d, operation = [%s]' % (id, opera)
        if opera == 'quit':
            break
    mia.set_step(1, 2, 3)
    for str in ['First RESULT', 'Second RESULT', 'Third RESULT']:
        mia.put_result(str)
