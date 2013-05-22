# set up stdard variables

Import('TOPDIR', 'BUILD_SYSTEM', '_p', '_inc')

SRC_TARGET_DIR=_p(TOPDIR, 'build/target')
PLATFORM_VERSION='2.0.1'
Export('SRC_TARGET_DIR', 'PLATFORM_VERSION')

_inc(BUILD_SYSTEM, 'envsetup.mk')

_inc(BUILD_SYSTEM, 'dumpvar.mk')
