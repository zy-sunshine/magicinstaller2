class MiRegister(object):
    def __init__(self):
        self.handlers_long = {}
        self.handlers_short = {}
    
    def server_handler(self, type_, func_name=None):
        def dec(func):
            name = func_name and func_name or func.__name__
            if type_ == 'long':
                self.handlers_long.setdefault(name, []).append(func)
            elif type_ == 'short':
                self.handlers_short.setdefault(name, []).append(func)
            else:
                raise Exception('%s Raise' % self.__class__, 'Regist "%s" method \
                        Not Support' % type_)
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