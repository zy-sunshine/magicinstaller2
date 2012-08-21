class MiRegister(object):
    def __init__(self):
        self.handlers_long = {}
        self.handlers_short = {}
    
    def server_handler(self, name):
        def dec(func):
            #import pdb; pdb.set_trace()
            if name == 'long':
                self.handlers_long.setdefault(func.__name__, []).append(func)
            elif name == 'short':
                self.handlers_short.setdefault(func.__name__, []).append(func)
            else:
                raise Exception('%s Raise' % self.__class__, 'Regist "%s" method \
                        Not Support' % name)
            return func

        return dec
    def __getitem__(self, name):
        if name == 'long':
            return self.handlers_long
        elif name == 'short':
            return self.handlers_short
        else:
            raise Exception('%s Raise' % self.__class__, 'Regist "%s" method \
                        Not Support' % name)
        return 

    def __str__(self):
        ret = 'Long:\n'
        for k, v in self.handlers_long.items():
            ret += '%s => %s\n' % (k, v)
        ret += 'Short:\n'
        for k, v in self.handlers_short.items():
            ret += '%s => %s\n' % (k, v)
        return ret