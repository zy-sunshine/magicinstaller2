import os
import threading
import simplejson as json
from miutils import printer

class MiConfig_SubCategory(object):
    def __init__(self, sself, section):
        self.__dict__['confobj'] = sself
        self.__dict__['section'] = section
    
    def __getattr__(self, key):
        confobj = self.__dict__['confobj']
        section = self.__dict__['section']
        #if not confobj.has_option(section, key):
        #    confobj.set(section, key, None)
        #try:
        #ret = self.__dict__['sself'].__dict__['confobj'][section][key]
        ret = confobj[section][key]
        #except:
        #    import pdb;pdb.set_trace()
        return ret

    def __setattr__(self, key, value):
        confobj = self.__dict__['confobj']
        section = self.__dict__['section']
        confobj[section][key] = value
        
    def items(self):
        confobj = self.__dict__['confobj']
        section = self.__dict__['section']
        return confobj[section].items()
        
class MiConfig(object):
    def __init__():
        "disable the __init__ method, and this config class current not thread safely"
    
    __inst = None # make it so-called private

    __lock = threading.Lock() # used to synchronize code

    @staticmethod
    def get_instance():
        MiConfig.__lock.acquire()
        if not MiConfig.__inst:
            MiConfig.__inst = object.__new__(MiConfig)
            object.__init__(MiConfig.__inst)
            printer.d('MiConfig.get_instance --> Create a MiConfig Instance\n')
            MiConfig.__inst.init()
        MiConfig.__lock.release()
        return MiConfig.__inst
        
    def init(self):
        self.__dict__['confobj'] = {}
        self.__dict__['secobjs'] = {}
        conf_file = os.path.dirname(os.path.abspath(__file__))+'/config.json'
        if not os.path.exists(conf_file):
            printer.exception('MiConfig.init --> Cannot load config file %s\n' % conf_file)
        self.load_from_file(conf_file)
        
    def __getattr__(self, key):
        confobj = self.__dict__['confobj']
        secobjs = self.__dict__['secobjs']
        return secobjs[key]
        
        
    def save_to_file(self, conf_file):
        printer.d('MiConfig.save_to_file --> %s\n' % conf_file)
        confobj = self.__dict__['confobj']
        with open(conf_file, 'w') as configfile:
            json.dump(self.__dict__['confobj'], fp=configfile, indent=4)
        
    def load_from_file(self, conf_file):
        printer.d('MiConfig.load_from_file --> %s\n' % conf_file)
        with open(conf_file, 'r') as configfile:
            self.__dict__['confobj'].clear()
            self.__dict__['confobj'].update(json.load(configfile))
        confobj = self.__dict__['confobj']
        secobjs = self.__dict__['secobjs']
        secobjs.clear()
        for key in confobj.keys():
            secobjs[key] = MiConfig_SubCategory(confobj, key)
        
    def dump(self):
        confobj = self.__dict__['confobj']
        secobjs = self.__dict__['secobjs']
        for key in self.secobjs.keys():
            for key, value in secobjs[key].items():
                print key, value

    def __del__(self):
        printer.d('MiConfig.__del__ --> %s' % self)

def TestMiConfig_SaveConfig():
    mc = MiConfig.get_instance()
    mc.LOAD.teststring = 'stringstring test test abcde'
    mc.RUN.pkgarr_probe = [['/dev/sda1', 'ntfs', '/dev/sda1'], ['/dev/sda2',
    'ntfs', '/dev/sda2'], ['/dev/sda5', 'linux-swap(v1)', '/dev/sda5'],
    ['/dev/sda6', 'ext3', '/dev/sda6'], ['/dev/sda7', 'ext4', '/dev/sda7'],
    ['/dev/sda8', 'ntfs', '/dev/sda8']]

    mc.save_to_file('t-config.json')
    mc2 = MiConfig.get_instance()
    mc.dump()
    print '-'*40
    mc2.dump()
    
def TestMiConfig_LoadConfig():
    mc = MiConfig.get_instance()
    mc2 = MiConfig.get_instance()
    mc2.load_from_file('t-config.json')
    mc.dump()
    print '-'*40
    mc2.dump()
    
def TestMiConfig_LoadConfig2():
    mc = MiConfig.get_instance()
    mc.load_from_file('t-config.json')
    mc.dump()
    print '-'*40
    mc2 = MiConfig.get_instance()
    mc2.load_from_file('/tmpfs/step_conf/step_3.json')
    mc.dump()
    
if __name__ == '__main__':
    TestMiConfig_SaveConfig()
    TestMiConfig_LoadConfig()
    TestMiConfig_LoadConfig2()