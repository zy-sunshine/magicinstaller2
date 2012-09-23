from gettext import gettext as _

from mi.utils import logger
from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()

class FakeMiactions(object):
    def set_step(self, operid, arg0, arg1):
        print 'mia.set_step( %d,  %d, %d )' % (operid, arg0, arg1)
