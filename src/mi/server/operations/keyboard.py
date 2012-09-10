#!/usr/bin/python
import os.path
import getdev
from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()

from mi.utils.miregister import MiRegister
register = MiRegister()
from mi.server.utils import logger
dolog = logger.info

@register.server_handler('short')
def config_keyboard():
    kbd = os.path.join(CF.D.TGTSYS_ROOT, 'etc/sysconfig/keyboard')
    os.system('echo KEYBOARDTYPE=\\"pc\\" > %s' % kbd)
    os.system('echo KEYTABLE=\\"us\\" >> %s' % kbd)
    return  0
