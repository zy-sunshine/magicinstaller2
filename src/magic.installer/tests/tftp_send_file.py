#!/usr/bin/python

import tftpc
cli = tftpc.TFtpClient()
cli.connect('192.168.56.111')
#localfn = '/var/log/sendFile'
localfn = '/home/sunshine/sendFile'
remotefn = 'recivedFile'
cli.put(localfn, remotefn)
