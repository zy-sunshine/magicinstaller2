from gettext import gettext as _

from miutils.milogger import ClientLogger
class Logger(object):
    @staticmethod
    def get_instance(TAG):
        return ClientLogger.get_instance(ClientLogger, TAG)
