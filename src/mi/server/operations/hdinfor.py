#!/usr/bin/python
import os
import string
from mi.utils.miregister import MiRegister
register = MiRegister()
from mi.server.utils import logger
dolog = logger.info

@register.server_handler('short')
def get_arch():
    (sysname, nodename, release, version, machine) = os.uname()
    if machine == 'i686':
        f = file('/proc/cpuinfo')
        cimap = {}
        l = f.readline()
        while l:
            a = string.split(l, ':')
            if len(a) == 2:
                (key, val) = string.split(l, ':')
                key = string.strip(key)
                val = string.strip(val)
                cimap[key] = val
            l = f.readline()
        f.close()
        if cimap.has_key('model name') and \
           string.find(string.lower(cimap['model name']), 'athlon') >= 0:
            machine = 'athlon'
    return machine
