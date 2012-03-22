import simplejson as json

class MiConfig(object):
    def __init__(self):
        self.__dict__['_settings'] = {}

    def __getattr__(self, key):
        return getattr(self.__dict__['_settings'], key, None)
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
if __name__ == '__main__':
    mc = MiConfig()
    mc.pkgarr_probe = [['/dev/sda1', 'ntfs', '/dev/sda1'], ['/dev/sda2',
    'ntfs', '/dev/sda2'], ['/dev/sda5', 'linux-swap(v1)', '/dev/sda5'],
    ['/dev/sda6', 'ext3', '/dev/sda6'], ['/dev/sda7', 'ext4', '/dev/sda7'],
    ['/dev/sda8', 'ntfs', '/dev/sda8']]

    mc.teststring = 'stringstring test test abcde'
    mc.save_to_file('config.json')
    mc2 = MiConfig()
    mc2.load_from_file('config.json')
    mc2.dump()
