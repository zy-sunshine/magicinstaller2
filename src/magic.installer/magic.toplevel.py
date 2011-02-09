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
import subprocess
from mipublic import *
import time
import signal

tee_pipe = subprocess.Popen(["/usr/bin/tee", "/var/log/magic.toplevel.log"],
                            stdin = subprocess.PIPE)
os.dup2(tee_pipe.stdin.fileno(), sys.stdout.fileno())
os.dup2(tee_pipe.stdin.fileno(), sys.stderr.fileno())

class FlushFile(object):
    """Write-only flushing wrapper for file-type objects."""
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()
    def fileno(self):
        return self.f.fileno()
    def flush(self):
        self.f.flush()

# Replace stdout with an automatically flushing version
sys.stdout = FlushFile(sys.__stdout__)
sys.stderr = FlushFile(sys.__stderr__)

# First is default layout
layoutopt = ['LayoutFb', 'LayoutVesa']

def file_path(filename):
    realFile = filename
    realFile = search_file(filename, [hotfixdir, '/usr/bin'], exit_if_not_found = False) or realFile
    realFile = search_file(filename+'.py', [hotfixdir, '/usr/bin'], exit_if_not_found = False) or realFile
    return realFile

def start_server(args, logfn):
    pid = os.fork()
    if pid == 0:
        logfd = os.open(logfn, os.O_CREAT | os.O_WRONLY, 0600)
        os.dup2(logfd, sys.stderr.fileno())
        os.dup2(logfd, sys.stdout.fileno())
        os.close(logfd) 
        os.execl(args[0], *args)
    return pid

def start_gui(args, logfn, layoutopt):
    ppid = os.fork()
    if ppid == 0:
        ret = 1
        pid = None
        def handler(signum, frame):
            if pid:
                os.kill(pid, signum)
        signal.signal(signal.SIGQUIT, handler)
        for layout in layoutopt:
            pid = os.fork()
            if pid == 0:
                logfd = os.open(logfn, os.O_CREAT | os.O_WRONLY, 0600)
                os.dup2(logfd, sys.stderr.fileno())
                os.dup2(logfd, sys.stdout.fileno())
                os.close(logfd)
                args.extend(['-layout', layout])
                os.execl(args[0], *args)
            status = 1
            try:
                if pid:
                    status = os.waitpid(pid, 0)[1]
            except OSError, e:
                if e.errno == 4:
                    # Interrupted system call, we don't really care about it.
                    status = 0
                    pass
            if status == 0:
                ret = 0
                break
            else:
                # resort to other layout if failed
                ret = 2
                print '\nWarning: Fall back to %s.' % layout
                print 'Pausing for 5 seconds...'
                time.sleep(5)
        os._exit(ret)
    return ppid

# Run logger Server
runfile = file_path('magic.actions.logger')
print runfile, "Running..."
logger_server_pid = start_server(['/usr/bin/python', runfile], 
        '/var/log/magic.actions.logger.log')
time.sleep(1)

# Run logger GUI
runfile = file_path('magic.logger')
print runfile, "Running..."
p_logger_pid = start_gui(['/usr/bin/xinit', '/usr/bin/python',
                 runfile, '--', '/usr/bin/X', ':1'],
                '/var/log/magic.logger.log', layoutopt)
time.sleep(1)

# Run MI Server
runfile = file_path('magic.actions')
print runfile, "Running..."
server_pid = start_server(['/usr/bin/python', runfile], 
        '/var/log/magic.actions.log')
time.sleep(1)

# Run MI GUI
runfile = file_path('magic.installer')
print runfile, "Running..."
p_installer_pid = start_gui(['/usr/bin/xinit', '/usr/bin/python',
                 runfile, '--', '/usr/bin/X', ':0'],
                '/var/log/magic.installer.log', layoutopt)

def wait_pid(pid):
    if pid:
        try:
            os.waitpid(pid, 0)
        except OSError, e:
            print str(e)
            print "wait pid %s failed" % pid
wait_pid(p_installer_pid)
os.kill(p_logger_pid, signal.SIGQUIT)
wait_pid(p_logger_pid)
os.system("%s > /dev/null 2>&1" % file_path("magic.actions.quit"))
os.system("%s > /dev/null 2>&1" % file_path("magic.actions.logger.quit"))
wait_pid(server_pid)
wait_pid(logger_server_pid)

#os.waitpid(actserver_pid, 0)
#os.waitpid(gui_pid, 0)

# probe for intel i8xx video cards
#import  rhpxl.videocard
#vci = rhpxl.videocard.VideoCardInfo()
#for vc in vci.videocards:
#    if vc.getDriver() == 'i810':
#        #os.system('/sbin/modprobe agpgart')
#        layoutopt = 'LayoutI810'
#        break

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
