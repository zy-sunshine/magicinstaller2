Import('env', 'TOPDIR', 'BUILD_SYSTEM', '_p', '_inc')

Import('*')

dumptag_map = {}
for tag in COMMAND_LINE_TARGETS:
    if tag.startswith('dumpvar-'):
        dumptag_map[tag] = tag[len('dumpvar-'):]


#env.Command(env.Alias(tag), '',
#    ['echo %s' % dumpv])
def _info(msg):
    print msg

def do_report_config():
    _info('============================================')
    _info('PLATFORM_VERSION = %s' % PLATFORM_VERSION)
    _info('TARGET_PRODUCT = %s' % TARGET_PRODUCT)
    _info('TARGET_BUILD_VARIANT = %s' % TARGET_BUILD_VARIANT)
    _info('TARGET_BUILD_TYPE = %s' % TARGET_BUILD_TYPE)
    _info('TARGET_BUILD_APPS = %s' % TARGET_BUILD_APPS)
    _info('TARGET_ARCH = %s' % TARGET_ARCH)
    _info('HOST_ARCH = %s' % HOST_ARCH)
    _info('HOST_OS = %s' % HOST_OS)
    _info('HOST_BUILD_TYPE = %s' % HOST_BUILD_TYPE)
    _info('BUILD_ID = %s' % BUILD_ID)
    _info('============================================')
def do_dump_products():
    ps = env['PRODUCTS']
    for name, product in ps.items():
        _info('==================== PRODUCT ========================')
        _info('PRODUCT_NAME = %s' % name)
        for k, v in product.items():
            if k != 'PRODUCT_NAME':
                _info('%s = %s' % (k, v))
        _info('======================================================')

for key, value in dumptag_map.items():
    if value == 'report_config':
        do_report_config()
        env.Alias(key)
    else:
        env.Alias(key, env.Command('', '',
            '%s = %s' % (key, locals().get('key') or globals().get('key') )))

if 'dump-products' in COMMAND_LINE_TARGETS:
    do_dump_products()
    env.Alias('dump-products')
