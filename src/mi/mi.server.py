#!/usr/bin/python
#coding=utf-8
import os
import xmlrpclib
import SimpleXMLRPCServer
import sys
import select
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
    server_quit = 0
    # Control process.
    # Run short operation and transfer long operation to action process.
    #from mi.utils.milogger import ServerLogger_Short, ServerLogger_Long
    from mi.server.utils import logger
    from mi.server import handlers_short
    logger.d('test short logger')

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
                    logger.d('Run short.%s() with %s,\n' % (method, params))
                result = handlers_short[method](*params)
                if CF.D.EXPERT_MODE:
                    logger.d('    which returns %r\n' % (result,))
                return result
            else: # This is a long operation.
                # Return the operation identifier to the caller.
                if CF.D.EXPERT_MODE:
                    logger.d('Put long.%s() with %s' % (method, params))
                    t = xmlrpclib.dumps(params, methodname=method, allow_none = 1)
                    #log_long.debug('%s' % t)
                id = mia.put_operation(t)
                if CF.D.EXPERT_MODE:
                    logger.d(', and get id %d.\n' % (id))
                return id

    class ReuseXMLRPCServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
        """Reuse server address for handy test."""
        allow_reuse_address = True

    class RequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
        def __init__(self, *args, **kwgs):
            SimpleXMLRPCServer.SimpleXMLRPCRequestHandler.__init__(self, *args, **kwgs)

            
    server = ReuseXMLRPCServer(  #SimpleXMLRPCServer.SimpleXMLRPCServer( \
        ('127.0.0.1', 1325),
        RequestHandler,
        None,
        allow_none=True)
    server.register_instance(MIAction())
    server.register_introspection_functions()

    while 1:
        try:
            server.handle_request()
        except select.error:
            print 'select.error exception'
        if server_quit:
            break
    # Block until the action process terminate.
    mia.wait_action_exit()

elif mia.pid == 0:
    # Action process. For long operation only.
    #from mi.utils import MiLogger
    #log_long = MiLogger('mi_long')
    from mi.server.utils import logger
    from mi.server import handlers_long
    logger.i('test long logger')
    while 1:
        (id, opera) = mia.get_operation()
        if opera == 'quit':
            break
        else:
            (params, method) = xmlrpclib.loads(opera)
            if handlers_long.has_key(method):
                if CF.D.EXPERT_MODE:
                    logger.d('Run long.%s() with %s and id %d,\n' % (method, params, id))
                exe_ok = True
                try:
                    result = handlers_long[method](mia, id, *params)
                except:
                    result = 'Exception: run method %s raise %s' % (method, str(sys.exc_info()[0:2]))
                    exe_ok = False
                    logger.e(result, exc_info = sys.exc_info())
                if CF.D.EXPERT_MODE:
                    logger.d('    which returns %r.\n' % (result,))
                
                mia.put_result(xmlrpclib.dumps((id, result, exe_ok), methodname=method, allow_none = 1))
            else:
                if CF.D.EXPERT_MODE:
                    logger.e('ERROR: NOT SUPPORTED method %s().\n' % method)
                logger.e('method %s NOT_SUPPORT' % method)
                exe_ok = False
                mia.put_result(xmlrpclib.dumps((id, 'method %s NOT_SUPPORT' % method, exe_ok), methodname=method, allow_none = 1))

