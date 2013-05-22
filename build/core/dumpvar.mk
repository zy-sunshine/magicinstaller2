Import('env', 'TOPDIR', 'BUILD_SYSTEM', '_p', '_inc')

Import('*')

dumptag_map = {}
for tag in COMMAND_LINE_TARGETS:
    if tag.startswith('dumpvar-'):
        dumptag_map[tag] = tag[len('dumpvar-'):]


#env.Command(env.Alias(tag), '',
#    ['echo %s' % dumpv])
def info(msg):
    print msg

def do_report_config():
    info('============================================')
    info('PLATFORM_VERSION=%s' % PLATFORM_VERSION)
    #info('TARGET_PRODUCT=%s' % TARGET_PRODUCT)
    #info('TARGET_BUILD_VARIANT=%s' % TARGET_BUILD_VARIANT)
    #info('TARGET_BUILD_TYPE=%s' % TARGET_BUILD_TYPE)
    #info('TARGET_BUILD_APPS=%s' % TARGET_BUILD_APPS)
    #info('TARGET_ARCH=%s' % TARGET_ARCH)
    #info('TARGET_ARCH_VARIANT=%s' % TARGET_ARCH_VARIANT)
    #info('HOST_ARCH=%s' % HOST_ARCH)
    #info('HOST_OS=%s' % HOST_OS)
    #info('HOST_BUILD_TYPE=%s' % HOST_BUILD_TYPE)
    #info('BUILD_ID=%s' % BUILD_ID)
    info('============================================')

for key, value in dumptag_map.items():
    if value == 'report_config':
        do_report_config()
        env.Alias(key)
    else:
        env.Alias(key, env.Command('', '',
            do_report_config))

