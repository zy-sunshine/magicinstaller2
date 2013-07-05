Import('env', '_my_dir')

LOCAL_PATH = _my_dir()

PRODUCT_NAME = "arch"

PRODUCTS = env['PRODUCTS']
if PRODUCT_NAME in PRODUCTS.keys():
	_error('There have two products with same name %s -%s -%s' % (PRODUCT_NAME, PRODUCTS[PRODUCT_NAME]['PRODUCT_DIR'], LOCAL_PATH))

myp = PRODUCTS[PRODUCT_NAME] = {}

myp['PRODUCT_NAME'] = PRODUCT_NAME
myp['PRODUCT_ROOTFS'] = "arch1"
myp['PRODUCT_MIKERNELVER'] = "2.6.35.4"
myp['PRODUCT_BRAND'] = "ArchLinux"
myp['PRODUCT_LOCALES'] = "zh_CN en_US"
myp['PRODUCT_MANUFACTURER'] = "Magic Team"
myp['PRODUCT_PATH'] = LOCAL_PATH
