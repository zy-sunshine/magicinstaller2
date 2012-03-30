import pdb
class TestConfig(object):
    def __getattr__(self, key):
        pdb.set_trace()
        if self.__dict__['_settings'].has_key(key):
            return self.__dict__['_settings'][key]
        else:
            return None
            
    def __setattr__(self, key, value):
        pdb.set_trace()
        self.__dict__['_settings'][key] = value
        
if __name__ == '__main__':
    tc = TestConfig()
    tc.abc.dfg = '1'