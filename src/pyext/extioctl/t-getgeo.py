#!/usr/bin/python

import extioctl
import sys

for devfn in sys.argv[1:]:
    geo = extioctl.HDIO_GETGEO(devfn)
    print geo
