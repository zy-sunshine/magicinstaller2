#!/usr/bin/python

import os
import sys
import time
import socket
import xmlrpclib
from mipublic import *

server = xmlrpclib.ServerProxy('http://127.0.0.1:325')

def get_result(run_id):
    for i in range(10):
        try:
            new_result_list = server.get_results()
        except socket.error:
            # get results failed.
            print 'Socket error'
            return  False
        for result_xmlstr in new_result_list:
            res_tuple = xmlrpclib.loads(result_xmlstr)
            id = res_tuple[0][0]
            result = res_tuple[0][1]
            method = res_tuple[1]  # Not used yet.
            if id != run_id:
                print 'WARNING: id != run_id in get_result().\n'
                    # Weird encountered.
                print 'Id=%d, result=%s' % (id, result)
                continue
            return result
        print 'No result yet, sleep and retry %d times' % (i+1)
        time.sleep(1)
    raise Exception('Timeout with no result, id=%d' % run_id)
    
def test_probe_mouse():
    id = server.probe_mouse(0)
    print get_result(id)

def test_gen_x_config_mouse(is_synaptics):
    x_settings = {}
    x_settings['monitor'] = \
        ('Vmware Monitor',      # name
         '30-71',               # horiz
         '50-160',              # vert
         )
    x_settings['videocard'] = \
        ('Vmware videocard',    # name
         'vmware',              # driver
         '8192',                # videoram
         )
    if is_synaptics:
        x_settings['mouse'] = \
            ('Synaptics Touch Pad', # name
             'IMPS/2',              # protocol
             'input/mice',          # device
             'yes',                 # xemu3
             'synaptics',           # shortname
             )
    else:
        x_settings['mouse'] = \
            ('Generic - 3 Buttons Mouse (USB)', # name
             'IMPS/2',              # protocol
             'input/mice',          # device
             'no',                 # xemu3
             'generic3usb',           # shortname
             )
    x_settings['modes'] = {}
    resmap = {640: '640x480', 800: '800x600', 1024: '1024x768', 1280: '1280x1024'}
    for depth in [8, 15, 16, 24]:
        for res in [1280, 1024, 800, 640]:
            x_settings['modes'].setdefault(str(depth), []).append(resmap[res])
    # wide mode
    x_settings['wide_mode'] = \
        ('',                    # x
         '',                    # y
         '',                    # depth
         '',                    # refresh
         )
    # misc
    x_settings['init'] = '5'
    x_settings['FontPathes'] = []

    print 'Invokde server.gen_x_config()'
    os.system('mkdir -p %s/etc' % tgtsys_root)
    os.system('echo "id:3:initdefault" > %s/etc/inittab' % tgtsys_root)
    id = server.gen_x_config(x_settings)
    print get_result(id)

test_probe_mouse()
test_gen_x_config_mouse(0)
