from t_jsonconfig import MiConfig
CONF = MiConfig()
CONF.pkgarr = ['aa', 'bb']
def GET_G_CONF():
    return CONF

class Status(object):
    def __init__(self):
        pass
    def dump(self):
        for key, value in self.__dict__.items():
            print '%s => %s' % (key, value)

STAT = Status()
STAT.DONE = 0
STAT.probe_arr = STAT.DONE

def GET_G_STAT():
    return STAT
class mi_main:
    def __init__(self):
        execfile('t_globalconfig_sub.py')
        stepsub = eval('mistep_sub()')
        stepsub.dosomething()

xgobj = mi_main()
print '-'*80
CONF.dump()
STAT.dump()
