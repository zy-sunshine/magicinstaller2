#!/usr/bin/python
#coding=utf-8
import os
import xmlrpclib
import SimpleXMLRPCServer
import sys
import miactions
from miutils.milogger import MiLogger
from miutils.miconfig import MiConfig
CONF = MiConfig.get_instance()

#CONF_DATADIR = CONF.LOAD.CONF_DATADIR
#os.chdir(CONF_DATADIR)
CONF_EXPERT_MODE = CONF.LOAD.CONF_EXPERT_MODE

try:
    miinitrd_pos
except:
    # Failed: Load the default values.
    miinitrd_pos = None

mia = miactions.MIActions(128, 128*1024, 128*1024)

if mia.pid > 0:
    # Control process.
    # Run short operation and transfer long operation to action process.
    from miutils.milogger import ServerLogger_Short, ServerLogger_Long
    log_short = ServerLogger_Short.get_instance(ServerLogger_Short, __name__)
    log_long = ServerLogger_Long.get_instance(ServerLogger_Long, __name__)
    def dolog(msg):
        log_short.i(msg)
    dolog('test short log')
    #print log.get_logpath(ServerLogger_Short)
    import short_operations

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
            if short_operations.__dict__.has_key(method):
                if CONF_EXPERT_MODE:
                    dolog('Run short.%s() with %s,\n' % (method, params))
                result = short_operations.__dict__[method](*params)
                if CONF_EXPERT_MODE:
                    dolog('    which returns %r\n' % (result,))
                return result
            else: # This is a long operation.
                # Return the operation identifier to the caller.
                if CONF_EXPERT_MODE:
                    log_long.d('Put long.%s() with %s' % (method, params))
                    t = xmlrpclib.dumps(params, methodname=method, allow_none = 1)
                    #log_long.d('%s' % t)
                id = mia.put_operation(t)
                if CONF_EXPERT_MODE:
                    log_long.d(', and get id %d.\n' % (id))
                return id

    class ReuseXMLRPCServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
        """Reuse server address for handy test."""
        allow_reuse_address = True

    server = ReuseXMLRPCServer(  #SimpleXMLRPCServer.SimpleXMLRPCServer( \
        ('127.0.0.1', 1325),
        SimpleXMLRPCServer.SimpleXMLRPCRequestHandler,
        None)
    server.register_instance(MIAction())
    while 1:
        server.handle_request()
        if server_quit:
            break
    # Block until the action process terminate.
    mia.wait_action_exit()
    log.del_instances()

elif mia.pid == 0:
    # Action process. For long operation only.
    from miutils.milogger import MiLogger
    from miutils.milogger import ServerLogger_Long
    log = ServerLogger_Long.get_instance(ServerLogger_Long, __name__)
    #print log.get_logpath(ServerLogger_Long)
    def dolog(msg):
        log.w(msg)
    dolog('test long log')
    import long_operations

    while 1:
        (id, opera) = mia.get_operation()
        if opera == 'quit':
            break
        else:
            (params, method) = xmlrpclib.loads(opera)
            if long_operations.__dict__.has_key(method):
                if CONF_EXPERT_MODE:
                    dolog('Run long.%s() with %s and id %d,\n' % (method, params, id))
                result = eval('long_operations.%s(mia, id, *params)' % method)
                if CONF_EXPERT_MODE:
                    dolog('    which returns %r.\n' % (result,))
                mia.put_result(xmlrpclib.dumps((id, result), methodname=method, allow_none = 1))
            else:
                if CONF_EXPERT_MODE:
                    dolog('ERROR: NOT SUPPORTED method %s().\n' % method, color_c.blue)
                mia.put_result(xmlrpclib.dumps((id, 'NOT_SUPPORT'), methodname=method, allow_none = 1))
    log.del_instances()
