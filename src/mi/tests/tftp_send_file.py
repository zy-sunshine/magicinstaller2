#!/usr/bin/python
import sys
sys.path.insert(0, '../libs')
import tftpc
cli = tftpc.TFtpClient()
cli.connect('127.0.0.1')
#localfn = '/var/log/sendFile'
localfn = '/home/sunshine/sendFile'
remotefn = 'recivedFile'
cli.put(localfn, remotefn)
