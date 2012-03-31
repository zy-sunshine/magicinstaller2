#!/usr/bin/python
from miutils.miconfig import MiConfig
CONF = MiConfig.get_instance()
CONF_KERNELVER = CONF.LOAD.CONF_KERNELVER
CONF_TGTSYS_ROOT = CONF.LOAD.CONF_TGTSYS_ROOT

from miutils.miregister import MiRegister
register = MiRegister()
from miserver.utils import Logger
Log = Logger.get_instance(__name__)
dolog = Log.i

@register.server_handler('short')
def get_all_scsi_modules():
    def scan_scsi_module_dir(the_list, dirname, name):
        mod_ext = os.uname()[2][:3] > '2.4' and '.ko' or '.o'
        for bn in name:
            filename = os.path.join(dirname, bn)
            if os.path.isfile(filename) and os.path.splitext(bn)[1] == mod_ext:
                the_list.append(os.path.splitext(bn)[0])

    scsi_module_list = []
    os.path.walk(os.path.join('/lib/modules', CONF_KERNELVER, 'kernel/drivers/scsi'),
                 scan_scsi_module_dir, scsi_module_list)
    return  scsi_module_list

@register.server_handler('short')
def get_all_loaded_modules():
    loaded_module_list = []
    mods = file('/proc/modules')
    l = mods.readline()
    while l:
        loaded_module_list.append(string.split(l)[0])
        l = mods.readline()
    mods.close()
    return  loaded_module_list


#--------------------------------------------------------

@register.server_handler('long')
def do_modprobe(mia, operid, module):
    def get_all_loaded_modules():
        loaded_module_list = []
        mods = file('/proc/modules')
        l = mods.readline()
        while l:
            loaded_module_list.append(string.split(l)[0])
            l = mods.readline()
        mods.close()
        return  loaded_module_list

    modlist = get_all_loaded_modules()
    if not 'sd_mod' in modlist:
        os.system('/sbin/modprobe sd_mod 2>/dev/null')
    if not module in modlist:
        os.system('/sbin/modprobe %s' % module)

    modlist = get_all_loaded_modules()
    return (module in modlist) #('sd_mod' in modlist) and (module in modlist)

@register.server_handler('long')
def scsi_modprobe_conf(mia, operid, scsi_module_list):
    mconf = file(os.path.join(CONF_TGTSYS_ROOT, 'etc/modules.conf'), 'a')
    mpconf = file(os.path.join(CONF_TGTSYS_ROOT, 'etc/modprobe.conf'), 'a')
    for module in string.split(scsi_module_list, '/'):
        mconf.write('alias scsi_hostadapter %s\n' % module)
        mpconf.write('alias scsi_hostadapter %s\n' % module)
    mpconf.close()
    mconf.close()
    return  0
