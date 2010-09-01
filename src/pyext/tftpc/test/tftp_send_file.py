#!/usr/bin/python

import tftpc
cli = tftpc.TFtpClient()
cli.connect('127.0.0.1')
localfn = '/home/sunshine/sendFile'
remotefn = 'recivedFile'
cli.put(localfn, remotefn)
