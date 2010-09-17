#!/usr/bin/python
# Copyright (C) 2003, Charles Wang.
# Author:  Charles Wang <charles@linux.net.cn>
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANT; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public LIcense for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.

import os
import xmlrpclib
import SimpleXMLRPCServer
import sys
sys.path.insert(0,'libs')
import miactions

from mipublic import *

os.chdir(DATADIR)

try:
    miinitrd_pos
    #execfile(os.path.join(MBRoot, 'mbresult.py'))
except:
    # Failed: Load the default values.
    miinitrd_pos = None

mia = miactions.MIActions(128, 128*1024, 128*1024)

if mia.pid > 0:
    # Control process.
    # Run short operation and transfer long operation to action process.
    openlog('/var/log/shortop.log')

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
                if EXPERT_MODE:
                    dolog('Run short.%s() with %s,\n' % (method, params))
                result = short_operations.__dict__[method](*params)
                if EXPERT_MODE:
                    dolog('    which returns %r\n' % (result,))
                return result
            else: # This is a long operation.
                # Return the operation identifier to the caller.
                if EXPERT_MODE:
                    dolog('Put long.%s() with %s' % (method, params))
                id = mia.put_operation(xmlrpclib.dumps(params, methodname=method, allow_none = 1))
                if EXPERT_MODE:
                    dolog(', and get id %d.\n' % (id))
                return id

    class ReuseXMLRPCServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
        """Reuse server address for handy test."""
        allow_reuse_address = True

    server = ReuseXMLRPCServer(  #SimpleXMLRPCServer.SimpleXMLRPCServer( \
        ('127.0.0.1', 325),
        SimpleXMLRPCServer.SimpleXMLRPCRequestHandler,
        None)
    server.register_instance(MIAction())
    while 1:
        server.handle_request()
        if server_quit:
            break
    # Block until the action process terminate.
    mia.wait_action_exit()
    closelog()

elif mia.pid == 0:
    # Action process. For long operation only.
    openlog('/var/log/longop.log')

    import long_operations

    while 1:
        (id, opera) = mia.get_operation()
        if opera == 'quit':
            break
        else:
            (params, method) = xmlrpclib.loads(opera)
            if long_operations.__dict__.has_key(method):
                if EXPERT_MODE:
                    dolog('Run long.%s() with %s and id %d,\n' % (method, params, id))
                result = eval('long_operations.%s(mia, id, *params)' % method)
                if EXPERT_MODE:
                    dolog('    which returns %r.\n' % (result,))
                mia.put_result(xmlrpclib.dumps((id, result), methodname=method, allow_none = 1))
            else:
                if EXPERT_MODE:
                    dolog('ERROR: NOT SUPPORTED method %s().\n' % method)
                mia.put_result(xmlrpclib.dumps((id, 'NOT_SUPPORT'), methodname=method, allow_none = 1))
    closelog()
