#!/usr/bin/python
#coding=utf8
import time
from mi.utils.miconfig import MiConfig
from mi.utils.common import run_bash, mount_dev, umount_dev, search_file
CONF = MiConfig.get_instance()
CONF_HOTFIXDIR = CONF.LOAD.CONF_HOTFIXDIR
from mi.utils.miregister import MiRegister
register = MiRegister()
from mi.server.utils import logger
dolog = logger.info

def copy_logfiles(logfiles, destdir):
    ret = []
    errormsg = []
    for logfile in logfiles:
        if not os.path.exists(logfile):
            continue
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        cmd_res = run_bash("cp",[ "-r", logfile, destdir])
        if cmd_res['ret']:
            ret.append(cmd_res['ret'])
            errormsg.append(cmd_res['err'])
    return ret, errormsg
    
@register.server_handler('long')
def logger_copy_logfiles(mia, operid, param):
    def start_operate(title):
        time.sleep(0.2)
        print title

    usb_dev_path, usb_fs_type, logfiles = param
    usb_mount_dir = ""
    steps = 4
    step = 0
    mia.set_step(operid, step, steps)
    # mount the usb device.
    step = step + 1
    mia.set_step(operid, step, steps)
    start_operate('Mount...')
    ret, msg = mount_dev(usb_fs_type, usb_dev_path)
    if not ret:
        return str(msg)
    else:
        usb_mount_dir = msg

    # Copy logfiles to usb.
    step = step + 1
    mia.set_step(operid, step, steps)
    start_operate('Copy logfiles...')
    ret, msg = copy_logfiles(logfiles, os.path.join(usb_mount_dir, "magiclogger"))
    if ret:
        return str(msg)
    
    step = step + 1
    mia.set_step(operid, step, steps)
    start_operate('Sync files...')
    run_bash('/bin/sync')

    # umount the usb device.
    step = step + 1
    mia.set_step(operid, step, steps)
    start_operate('Umount...')
    ret, msg = umount_dev(usb_mount_dir)
    if not ret:
        return str(msg)

    return 0

def file_path(filename):
    realFile = filename
    realFile = search_file(filename, [CONF_HOTFIXDIR, '/usr/bin'], exit_if_not_found = False) or realFile
    realFile = search_file(filename+'.py', [CONF_HOTFIXDIR, '/usr/bin'], exit_if_not_found = False) or realFile
    return realFile
    
@register.server_handler('long')
def start_magiclogger(mia, operid, param):
    os.system("/usr/bin/xinit /usr/bin/python %s -- /usr/bin/X :1" % file_path("magic.logger"))
    return 0

