import os, sys
import glob

Import('TOPDIR')

def get_all_product_makefiles():
    miproducts = glob.glob('%s/vendor/*/*/MiProducts.mk' % TOPDIR)
    makefiles = []
    for p in miproducts:
        sys.argv = [os.path.basename(p), os.path.dirname(p), ]
        gmap = {}
        lmap = {}
        execfile(p, gmap, lmap)
        makefiles.extend(lmap['PRODUCT_MAKEFILES'])
    for m in makefiles:
        if not os.path.exists(m):
            raise Exception("Can not locate product make file %s" % m)
    return makefiles

Export('get_all_product_makefiles')

