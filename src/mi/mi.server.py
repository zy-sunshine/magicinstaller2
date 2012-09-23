#!/usr/bin/python
#coding=utf-8
import os
import xmlrpclib
import SimpleXMLRPCServer
import sys
import miactions
from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()

try:
    miinitrd_pos
except:
    # Failed: Load the default values.
    miinitrd_pos = None

mia = miactions.MIActions(128, 128*1024, 128*1024)

if mia.pid > 0:
    # Control process.
    # Run short operation and transfer long operation to action process.
    #from mi.utils.milogger import ServerLogger_Short, ServerLogger_Long
    from mi.utils import MiLogger
    log_short = MiLogger("mi_short")
    log_long = MiLogger("mi_long")
    from mi.server import handlers_short
    def dolog(msg):
        log_short.w(msg)
    dolog('test short logger')
    server_quit = 0

    class MIAction:
        def _dispatch(self, method, params):
            global  server_quit
            if method == 'quit':
                mia.put_operation('quit')
                server_quit = 1
                return 0
            elif method == 'get_results':
                result_list = mia.get_result()
                return  result_list
            elif method == 'probe_step':
                return  mia.probe_step()
            if handlers_short.has_key(method):
                if CF.D.EXPERT_MODE:
                    dolog('Run short.%s() with %s,\n' % (method, params))
                result = handlers_short[method](*params)
                if CF.D.EXPERT_MODE:
                    dolog('    which returns %r\n' % (result,))
                return result
            else: # This is a long operation.
                # Return the operation identifier to the caller.
                if CF.D.EXPERT_MODE:
                    log_long.w('Put long.%s() with %s' % (method, params))
                    t = xmlrpclib.dumps(params, methodname=method, allow_none = 1)
                    #log_long.debug('%s' % t)
                id = mia.put_operation(t)
                if CF.D.EXPERT_MODE:
                    log_long.w(', and get id %d.\n' % (id))
                return id

    class ReuseXMLRPCServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
        """Reuse server address for handy test."""
        allow_reuse_address = True

    class RequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
        def __init__(self, *args, **kwgs):
            SimpleXMLRPCServer.SimpleXMLRPCRequestHandler.__init__(self, *args, **kwgs)
#            self.do_OPTIONS = self.do_POST
#            self.do_GET = self.do_POST
#        def do_GET(self):
#            print 'do_GET'
#            return self.do_POST()

#        def do_OPTIONS(self):
#            print 'do_OPTIONS'
#            return self.do_POST()
##            print 'self.path %s' % self.path 
##            if self.path in ('*', '/list'):
##                self.send_response(200)
##                self.send_header('Allow', 'GET, OPTIONS')
##                self.send_header('Access-Control-Allow-Origin', '*')
##                self.send_header('Access-Control-Allow-Headers', 'X-Request, X-Requested-With')
##            else:
##                self.send_response(404)
##            self.send_header('Content-Length', '0')
##            self.end_headers()
#        def do_GET(self):
#            print 'do_GET'
#            return self.do_POST()
##            print 'self.path %s' % self.path 
##            if self.path in ('*', '/list'):
##                self.send_response(200)
##                self.send_header('Allow', 'GET, OPTIONS')
##                self.send_header('Access-Control-Allow-Origin', '*')
##                self.send_header('Access-Control-Allow-Headers', 'X-Request, X-Requested-With')
##            else:
##                self.send_response(404)
##            self.send_header('Content-Length', '0')
##            self.end_headers()
            
    server = ReuseXMLRPCServer(  #SimpleXMLRPCServer.SimpleXMLRPCServer( \
        ('127.0.0.1', 1325),
        RequestHandler,
        None,
        allow_none=True)
    server.register_instance(MIAction())
    server.register_introspection_functions()
    while 1:
        server.handle_request()
        if server_quit:
            break
    # Block until the action process terminate.
    mia.wait_action_exit()

elif mia.pid == 0:
    # Action process. For long operation only.
    from mi.utils import MiLogger
    log_long = MiLogger('mi_long')
    from mi.server import handlers_long
    def dolog(msg):
        log_long.w(msg)
    dolog('test long logger')
    while 1:
        (id, opera) = mia.get_operation()
        if opera == 'quit':
            break
        else:
            (params, method) = xmlrpclib.loads(opera)
            if handlers_long.has_key(method):
                if CF.D.EXPERT_MODE:
                    dolog('Run long.%s() with %s and id %d,\n' % (method, params, id))
                try:
                    result = handlers_long[method](mia, id, *params)
                except:
                    result = 'run method %s raise exception %s' % (method, str(sys.exc_info()[0:2]))
                    log_long.e(result)
                if CF.D.EXPERT_MODE:
                    dolog('    which returns %r.\n' % (result,))
                mia.put_result(xmlrpclib.dumps((id, result), methodname=method, allow_none = 1))
            else:
                if CF.D.EXPERT_MODE:
                    dolog('ERROR: NOT SUPPORTED method %s().\n' % method)
                log_long.w('method %s NOT_SUPPORT' % method)
                mia.put_result(xmlrpclib.dumps((id, 'NOT_SUPPORT'), methodname=method, allow_none = 1))

#if mia.pid > 0:
    #from mi.utils.milogger import ServerLogger_Short, ServerLogger_Long
    #print ServerLogger_Short.get_logpath(ServerLogger_Short)
    #print ServerLogger_Long.get_logpath(ServerLogger_Long)
    #ServerLogger_Long.del_instances(ServerLogger_Long)
    #ServerLogger_Short.del_instances(ServerLogger_Short)
    ##log_short = ServerLogger_Short.get_instance(ServerLogger_Short, __name__)
    ##log_short.del_instances(ServerLogger_Short)
    #log_long = ServerLogger_Long.get_instance(ServerLogger_Long, __name__)
    #log_long.del_instances(ServerLogger_Long)