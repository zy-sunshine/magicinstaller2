Import('env', '_my_dir')

LOCAL_PATH = _my_dir()

# Note: must same as TARGET_PRODUCT, from lunch item which format is TARGET_PRODUCT-TARGET_BUILD_VARIANT (eg. magic-eng )
PRODUCT_NAME = "magic"

PRODUCTS = env['PRODUCTS']
if PRODUCT_NAME in PRODUCTS.keys():
    _error('There have two products with same name %s -%s -%s' % (PRODUCT_NAME, PRODUCTS[PRODUCT_NAME]['PRODUCT_DIR'], LOCAL_PATH))

myp = PRODUCTS[PRODUCT_NAME] = {}

myp['PRODUCT_NAME'] = PRODUCT_NAME
myp['PRODUCT_DEVICE'] = "magic1"
myp['PRODUCT_BRAND'] = "MagicLinux"
myp['PRODUCT_MODEL'] = "MLJingyou"
myp['PRODUCT_HARDWARE_VERSION'] = "x86_full"
myp['BUILD_DISPLAY_ID'] = "MagicLinuxJingyou"
myp['PRODUCT_LOCALES'] = "zh_CN en_US"
myp['PRODUCT_MANUFACTURER'] = "MagicLinux Team"
myp['PRODUCT_PATH'] = LOCAL_PATH
