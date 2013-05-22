#!/usr/bin/python
# Note: this is a script, not a SConscript, executed by product.mk

import os, sys

LOCAL_PATH = sys.argv[1]

PRODUCT_MAKEFILES = [os.path.join(LOCAL_PATH, 'arch1.mk'), ]

