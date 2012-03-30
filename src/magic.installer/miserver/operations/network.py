#!/usr/bin/python
import os.path
import getdev

from miutils.miconfig import MiConfig
CONF = MiConfig.get_instance()
CONF_TGTSYS_ROOT = CONF.LOAD.CONF_TGTSYS_ROOT

from miutils.miregister import MiRegister
register = MiRegister()

@register.server_handler('short')
def config_network_short(hostname):
    hosts = os.path.join(CONF_TGTSYS_ROOT, 'etc/hosts')

    outhn = hostname
    if hostname != '':
        outhn = hostname + ' '
    else:
        outhn = 'localhost'
    os.system('echo -e "127.0.0.1\t%slocalhost.localdomain localhost" > %s' % (outhn, hosts))

    networkdir = os.path.join(CONF_TGTSYS_ROOT, 'etc/sysconfig')
    network = os.path.join(networkdir, 'network')
    os.system('mkdir -p %s' % networkdir)
    os.system('echo NETWORKING=yes > %s' % network)

    if hostname == '':
        outhn = 'localhost'
    else:
        outhn = hostname
    os.system('echo HOSTNAME=%s >> %s' % (outhn, network))

    HOSTNAME = os.path.join(CONF_TGTSYS_ROOT, 'etc/HOSTNAME')
    os.system('echo %s > %s' % (outhn, HOSTNAME))

    resolv_conf = os.path.join(CONF_TGTSYS_ROOT, 'etc/resolv.conf')
    os.system('echo /dev/null > %s' % resolv_conf)
    os.system('chmod 644 %s' % resolv_conf)

    return  0
