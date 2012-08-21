import logging, logging.config

logging.config.fileConfig("logging.conf")

#create logger
logger = logging.getLogger("mi_server")


from gettext import gettext as _

class FakeMiactions(object):
    def set_step(self, operid, arg0, arg1):
        print 'mia.set_step( %d,  %d, %d )' % (operid, arg0, arg1)
        