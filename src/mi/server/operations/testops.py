#!/usr/bin/python
import time
from mi.utils.miregister import MiRegister
register = MiRegister()
from mi.server.utils import logger
dolog = logger.info

@register.server_handler('long')
def sleep(mia, operid, sleepsec):
    for step in range(sleepsec):
        mia.set_step(operid, step, sleepsec)
        time.sleep(1)
    return 0
