#!/usr/bin/python
import parted
import kudzu
import os

if 1:
    if 1:
        def get_device_list():
            result = []
            hd_list = kudzu.probe(kudzu.CLASS_HD,
                                  kudzu.BUS_IDE | kudzu.BUS_SCSI | kudzu.BUS_MISC,
                                  kudzu.PROBE_ALL)
            print hd_list
            #for hd in hd_list:
            #    try:
            #        dev = parted.PedDevice.get(os.path.join('/dev/', hd.device))
            #    except:
            #        pass
            #    else:
            #        result.append(dev)
            #return result

print get_device_list()
