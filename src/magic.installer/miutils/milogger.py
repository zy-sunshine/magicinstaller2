#!/usr/bin/python
import simplejson as json
import threading
from datetime import datetime
import time
from miutils import printer
from miconfig import MiConfig
CONF = MiConfig.get_instance()
CONF_LOG_FILE = CONF.LOAD.CONF_LOG_FILE
CONF_DOLOG = CONF.LOAD.CONF_DOLOG


class MiLogger(object):
    def __init__():
        "disable the __init__ method"

    __insts = {} # make it so-called private

    __lock = threading.Lock() # used to synchronize code
    __logpath = CONF_LOG_FILE
        
    __logf = None
    __logf_opened = False
    __logf_ref_c = 0
    
    @staticmethod
    def get_instance(Class, TAG):
        Class.__lock.acquire()
        if not Class.__insts.has_key(TAG):
            Class.__insts[TAG] = object.__new__(Class)
            object.__init__(Class.__insts[TAG])
            printer.d('MiLogger.get_instance --> Create a MiLogger Instance: %s %s Class: %s\n' % (TAG, Class.__insts[TAG], hex(id(Class))))
            Class.__lock.release()
            Class.__insts[TAG].init(TAG)
            Class.__lock.acquire()
        Class.__lock.release()
        return Class.__insts[TAG]
        
    @staticmethod
    def del_instances(Class):
        for key in Class.__insts.keys():
            Class.__insts[key].uninit()
            Class.__insts[key] = None
            
    @staticmethod
    def set_logpath(Class, path):
        Class.__logpath = path
        
    @staticmethod
    def get_logpath(Class):
        return Class.__logpath
    
    def init(self, TAG):
        self.TAG = TAG
        #self.openlog(self.__logpath)  ### some error to log file. remove it temporary.
        
    def openlog(self, filename):
        self.__lock.acquire()
        if self.__logf_opened:
            self.__logf_ref_c += 1
            self.__lock.release()
            return
        if CONF_DOLOG:
            self.__logf = open(filename, 'w')
            self.__logf_opened = True
            printer.d('MiLogger.openlog --> Open file %s\n' % filename)
            self.__logf_ref_c += 1
        self.__lock.release()

    def dolog(self, msg, *args, **kw):
        self.__lock.acquire()
        msg = '[%s][%s][%s]%s\n' % ( datetime.now(), 
                                    kw.has_key('mtype') and kw['mtype'] or 'NORM',
                                    self.TAG, msg.strip())
        #if CONF_DOLOG and self.__logf:
        #    self.__logf.write(msg) ### some error to log file. remove it temporary.
        #    self.__logf.flush()
        if kw.has_key('pr'):
            kw['pr'](msg)
        self.__lock.release()
            
    def i(self, msg, *args, **kw):
        self.dolog(msg, mtype='INFO', pr = printer.i)
        
    def d(self, msg, *args, **kw):
        self.dolog(msg, mtype='DEBUG', pr = printer.d)
        
    def w(self, msg, *args, **kw):
        self.dolog(msg, mtype='WARNING', pr = printer.w)
        
    def e(self, msg, *args, **kw):
        self.dolog(msg, mtype='ERROR', pr = printer.e)
        
    def exception(self, msg, *args, **kw):
        self.dolog(msg, mtype='EXCEPTION', pr = printer.exception)
        
    def closelog(self):
        self.__lock.acquire()
        if CONF_DOLOG:
            self.__logf_ref_c -= 1
            if self.__logf_ref_c != 0:
                self.__lock.release()
                return
            else:
                if self.__logf:
                    printer.d('MiLogger.closelog --> Close file %s\n' % self.__logpath)
                    self.__logf.close()
        self.__lock.release()

    def uninit(self):
        printer.d('MiLogger.uninit --> del %s\n' % self)
        #self.closelog() ### some error to log file. remove it temporary.
        
def GetSingleLoggerClass(classname, logpath):
    newClass = type(classname, (MiLogger,), {})
    newClass.set_logpath(newClass, logpath)
    return newClass

__logger_map = { 'ClientLogger': '/var/log/mi/client.log', 
                              'ServerLogger_Short': '/var/log/mi/server-short.log', 
                              'ServerLogger_Long': '/var/log/mi/server-long.log', 
                              }
for __logger, __logpath in __logger_map.items():
    #### Create Logger classes
    exec('%s = GetSingleLoggerClass("%s", "%s")' % (__logger, __logger, __logpath))
#print ServerLogger_Short.get_logpath(ServerLogger_Short)
#print ServerLogger_Long.get_logpath(ServerLogger_Long)
#import sys
#sys.exit(0)
### -------- Test MiLogger --------------
TAG_LST = ['actions.long', 'actions.short', 'logger', 'modules', 'magic.installer']
LEN = 5
import random
class ThreadTest(threading.Thread):
    """Thread Test"""
    def __init__(self, LoggerClass):
        threading.Thread.__init__(self)
        self.s = random.randrange(0, LEN)
        self.idle_t = (random.randrange(0, 3) + 0.1) / 10
        self.logname = TAG_LST[self.s]
        self.LoggerClass = LoggerClass

    def run(self):
        c = 0
        logger = self.LoggerClass.get_instance(self.LoggerClass, self.logname)
        while(True):
            if c - 3 > self.s:
                break
            c += 1
            logger.i('thread %s count: %s' % (threading.current_thread(), c))
            time.sleep(self.idle_t)
            
def TestMiLogger():
    ''' Get A Logger Class and create single object with it, then use it do log '''
    LoggerClass = GetSingleLoggerClass('TestxxLogger', '/var/log/mi/TestxxLogger.log')
    logger = LoggerClass.get_instance(LoggerClass, TAG_LST[0])
    thread_pool = []
    for i in range(3):
         t = ThreadTest(LoggerClass)
         t.start()
         thread_pool.append(t)
         
    for t in thread_pool:
        t.join()
    LoggerClass.del_instances(LoggerClass)
    
def TestColorMiLogger():
    ''' A simple color logger test '''
    logger = MiLogger.get_instance(MiLogger, TAG_LST[0])
    logger.i('Information log message')
    logger.d('Debug log message')
    logger.w('Warning log message')
    logger.e('Error log message')
    logger.exception('Exception log message')
    MiLogger.del_instances(MiLogger)
    
if __name__ == '__main__':
    TestMiLogger()
    #TestColorLogger()
