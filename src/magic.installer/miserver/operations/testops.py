#!/usr/bin/python
import time
from miutils.miregister import MiRegister
register = MiRegister()
from miserver.utils import Logger
Log = Logger.get_instance(__name__)
dolog = Log.i

@register.server_handler('long')
def sleep(mia, operid, sleepsec):
    for step in range(sleepsec):
        mia.set_step(operid, step, sleepsec)
        time.sleep(1)
    return 0
