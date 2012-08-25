#!/usr/bin/python

import tftpc
import os
cli = tftpc.TFtpClient()
cli.connect('127.0.0.1', 69)
os.system('echo "test file content" > /tmp/test_upload_tftpc')
localfn = '/tmp/test_upload_tftpc'
remotefn = 'recivedFile'
cli.put(localfn, remotefn)
os.system('rm /tmp/test_upload_tftpc')
