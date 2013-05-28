#!/usr/bin/python
import os
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

authorizer = DummyAuthorizer()
ftp_home = "/tmpfs/tftpboot"
if not os.path.exists(ftp_home):
    os.makedirs(ftp_home)
authorizer.add_user("root", "magic", ftp_home, perm="elradfmw")
#authorizer.add_anonymous("/home/nobody")

handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer(("127.0.0.1", 21), handler)
server.serve_forever()
