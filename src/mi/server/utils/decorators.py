from mi.utils.miconfig import MiConfig
from mi.server.utils import logger
CF = MiConfig.get_instance()

def probe_cache(name):
    def dec(func):
        def wrap_func(*args, **kwargs):
            had_probe = getattr(CF.S, 'had_probe_%s' % name)
            if had_probe:
                logger.i('%s: %s have been probed' % (func.__name__, name))
                return getattr(CF.S, name)
            
            ret = func(*args, **kwargs)
            setattr(CF.S, 'had_probe_%s' % name, True)
            setattr(CF.S, name, ret)
            return ret
        return wrap_func

    return dec