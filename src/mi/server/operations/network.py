#!/usr/bin/python
import os.path

from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()

from mi.utils.miregister import MiRegister
register = MiRegister()
from mi.server.utils import logger
dolog = logger.info

@register.server_handler('short')
def config_network_short(hostname):
    hosts = os.path.join(CF.D.TGTSYS_ROOT, 'etc/hosts')

    outhn = hostname
    if hostname != '':
        outhn = hostname + ' '
    else:
        outhn = 'localhost'
    os.system('echo -e "127.0.0.1\t%slocalhost.localdomain localhost" > %s' % (outhn, hosts))

    networkdir = os.path.join(CF.D.TGTSYS_ROOT, 'etc/sysconfig')
    network = os.path.join(networkdir, 'network')
    os.system('mkdir -p %s' % networkdir)
    os.system('echo NETWORKING=yes > %s' % network)

    if hostname == '':
        outhn = 'localhost'
    else:
        outhn = hostname
    os.system('echo HOSTNAME=%s >> %s' % (outhn, network))

    HOSTNAME = os.path.join(CF.D.TGTSYS_ROOT, 'etc/HOSTNAME')
    os.system('echo %s > %s' % (outhn, HOSTNAME))

    resolv_conf = os.path.join(CF.D.TGTSYS_ROOT, 'etc/resolv.conf')
    os.system('echo /dev/null > %s' % resolv_conf)
    os.system('chmod 644 %s' % resolv_conf)

    return  0
