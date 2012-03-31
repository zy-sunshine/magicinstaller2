from miutils.milogger import ServerLogger_Short, ServerLogger_Long
class LoggerShort(object):
    @staticmethod
    def get_instance(TAG):
        return ServerLogger_Short.get_instance(ServerLogger_Short, TAG)
        
class LoggerLong(object):
    @staticmethod
    def get_instance(TAG):
        return ServerLogger_Long.get_instance(ServerLogger_Long, TAG)
        
class Logger(object):
    @staticmethod
    def get_instance(TAG):
        return ServerLogger_Long.get_instance(ServerLogger_Long, TAG)
        
def delete_log():
    #### TODO: fix multi process do log action
    ServerLogger_Short.del_instances(ServerLogger_Short)
    ServerLogger_Long.del_instances(ServerLogger_Long)
    
from gettext import gettext as _

class FakeMiactions(object):
    def set_step(self, operid, arg0, arg1):
        print 'mia.set_step( %d,  %d, %d )' % (operid, arg0, arg1)
        