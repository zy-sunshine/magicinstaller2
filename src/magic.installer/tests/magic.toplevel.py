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
import sys

from mipublic import *

actserver_pid = os.fork()
if actserver_pid == 0:
    logfd = os.open('/var/log/magic.actions.server.log', os.O_CREAT | os.O_WRONLY, 0600)
    os.dup2(logfd, 2)
    os.close(logfd)
    os.execl('/usr/bin/python', '/usr/bin/python', '/usr/bin/magic.actions.server')

# default layout
layoutopt = 'LayoutFb'


# probe for intel i8xx video cards
import  rhpxl.videocard
vci = rhpxl.videocard.VideoCardInfo()
for vc in vci.videocards:
    if vc.getDriver() == 'i810':
        #os.system('/sbin/modprobe agpgart')
        layoutopt = 'LayoutI810'
        break
while layoutopt:
    gui_pid = os.fork()
    if gui_pid == 0:
        logfd = os.open('/var/log/magicinstaller.log', os.O_CREAT | os.O_WRONLY, 0600)
        os.dup2(logfd, 2)
        os.close(logfd)
        os.execl('/usr/bin/xinit', '/usr/bin/xinit',
                 './gtk_bmp', '--',
                 '/usr/bin/X', '-layout', layoutopt, ':0')

    status = os.waitpid(gui_pid, 0)[1]
    # resort to VESA if failed
    if status == 0 or layoutopt == 'LayoutVesa':
        layoutopt = ''
    else:
        import time
        print '\nWarning: Fall back to VESA.'
        print 'Pausing for 5 seconds...'
        time.sleep(5)
        layoutopt = 'LayoutVesa'

os.waitpid(actserver_pid, 0)
#os.waitpid(gui_pid, 0)

## The follow code is deprecated.
##videos = kudzu.probe(kudzu.CLASS_VIDEO, kudzu.BUS_PCI, kudzu.PROBE_ALL)
##if videos:
##    video_driver = videos[0].driver.lower()
##    if 'intel' in video_driver:
##        for model in ['810', '815', '815e', '830',
##                      '845', '852', '855', '865']:
##            if model in video_driver:
##                layoutopt = 'LayoutI810'
##                #screenopt = 'ScreenI810'
##                #os.system('/sbin/modprobe agpgart')
##                break
#
##while 1:
##    os.write(2, 'Probe mouse...\n')
##    mouse = kudzu.probe(kudzu.CLASS_MOUSE, kudzu.BUS_PSAUX, kudzu.PROBE_ALL)
##    if mouse != []:
##        mouseopt = 'PS2Mouse'
##        os.write(2, 'A PS/2 Mouse is found.\n')
##        break
##    mouse = kudzu.probe(kudzu.CLASS_MOUSE, kudzu.BUS_USB, kudzu.PROBE_ALL)
##    if mouse != []:
##        mouseopt = 'USBMouse'
##        os.write(2, 'An USB Mouse is found.\n')
##        break
##    os.write(2, 'Not any mouse can be found (PS2 mouse and USB mouse are supported), sleep 2 seconds.\n')
##    time.sleep(2)
##os.execl('/usr/bin/xinit', '/usr/bin/xinit',
##         '/usr/bin/magic.installer', '--',
##         '/usr/bin/X', '-screen', screenopt, '-pointer', mouseopt, ':0')
