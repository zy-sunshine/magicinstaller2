import simplejson as json
import threading
from miutil import printl, color_c

class MiLogger(object):
    def __init__():
        "disable the __init__ method"

    def __getattr__(self, key):
        if self.__dict__['_settings'].has_key(key):
            return self.__dict__['_settings'][key]
        else:
            return None
            
    def __setattr__(self, key, value):
        self.__dict__['_settings'][key] = value
        
    def save_to_file(self, conf_file):
        f = open(conf_file, 'w')
        json.dump(self.__dict__['_settings'], fp=f, indent=4)
        f.close()
        
    def load_from_file(self, conf_file):
        f = open(conf_file)
        self.__dict__['_settings'] = json.load(f)
        f.close()
        
    def dump(self):
        for key, value in self.__dict__['_settings'].items():
            print '%s => %s' % (key, value)

    __inst = None # make it so-called private

    __lock = threading.Lock() # used to synchronize code

    @staticmethod
    def get_instance():
        MiConfig.__lock.acquire()
        if not MiConfig.__inst:
            MiConfig.__inst = object.__new__(MiConfig)
            object.__init__(MiConfig.__inst)
            MiConfig.__inst.__dict__['_settings'] = {'hotfixdir': '/tmp/update'}
            printl('Create an MiConfig Instance\n', color_c.red)
        MiConfig.__lock.release()
        return MiConfig.__inst
        
if __name__ == '__main__':
    mc = MiConfig.get_instance()
    mc.pkgarr_probe = [['/dev/sda1', 'ntfs', '/dev/sda1'], ['/dev/sda2',
    'ntfs', '/dev/sda2'], ['/dev/sda5', 'linux-swap(v1)', '/dev/sda5'],
    ['/dev/sda6', 'ext3', '/dev/sda6'], ['/dev/sda7', 'ext4', '/dev/sda7'],
    ['/dev/sda8', 'ntfs', '/dev/sda8']]

    mc.teststring = 'stringstring test test abcde'
    mc.save_to_file('config.json')
    mc2 = MiConfig.get_instance()
    mc.dump()
    print '-'*40
    mc2.dump()
    #mc2.load_from_file('config.json')
    #mc2.dump()
