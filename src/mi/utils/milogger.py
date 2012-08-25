#!/usr/bin/python
from mi.utils import printer
from datetime import datetime

class MiLogger(object):
    def __init__(self, name):
        import logging, logging.config
        logging.config.fileConfig('logging.conf')
        self.logger = logging.getLogger(name)
        self.usecolor = False
        self.TAG = name
        self.info = self.i
        self.debug = self.d
        self.error = self.e
        self.warning = self.w
        
    def print_msg(self, msg, *args, **kw):
        msg = '[%s][%s][%s]%s\n' % ( datetime.now(), 
                                    kw.has_key('mtype') and kw['mtype'] or 'NORM',
                                    self.TAG, msg.strip())
        if self.usecolor and kw.has_key('pr'):
            kw['pr'](msg)
        else:
            printer.printl(msg)
            
    def i(self, msg, *args, **kw):
        self.logger.info(msg)
        self.print_msg(msg, mtype='INFO', pr = printer.i)
        
    def d(self, msg, *args, **kw):
        self.logger.info(msg)
        self.print_msg(msg, mtype='DEBUG', pr = printer.d)
        
    def w(self, msg, *args, **kw):
        self.logger.info(msg)
        self.print_msg(msg, mtype='WARN', pr = printer.w)
        
    def e(self, msg, *args, **kw):
        self.logger.info(msg)
        self.print_msg(msg, mtype='ERROR', pr = printer.e)
        
    def exception(self, msg, *args, **kw):
        self.logger.info(msg)
        self.print_msg(msg, mtype='EXCEPTION', pr = printer.exception)
