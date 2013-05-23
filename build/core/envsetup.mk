import os
Import('BUILD_SYSTEM', '_p', '_inc')

TARGET_PRODUCT = os.environ.get('TARGET_PRODUCT')
TARGET_BUILD_TYPE = os.environ.get('TARGET_BUILD_TYPE')
TARGET_BUILD_VARIANT = os.environ.get('TARGET_BUILD_VARIANT')
TARGET_BUILD_APPS = os.environ.get('TARGET_BUILD_APPS')
BUILD_ID = os.environ.get('BUILD_ID')
BUILD_NUMBER = os.environ.get('BUILD_NUMBER')

uname = os.uname()
# ('Linux', 'arch32', '3.9.2-1-ARCH', '#1 SMP PREEMPT Sat May 11 21:11:14 CEST 2013', 'i686')
# HOST_OS
HOST_OS = uname[0]

# # BUILD_OS is the real host doing the build.
# BUILD_OS := $(HOST_OS)

# HOST_ARCH
HOST_ARCH = uname[-1]

# BUILD_ARCH := $(HOST_ARCH)

HOST_BUILD_TYPE = 'release'
Export('TARGET_PRODUCT', 'TARGET_BUILD_TYPE', 'TARGET_BUILD_VARIANT', 
	'TARGET_BUILD_APPS', 'HOST_ARCH', 'HOST_OS', 'HOST_BUILD_TYPE',
	'BUILD_ID', 'BUILD_NUMBER')


### Custom variables in product_config.mk

# Set up version information.
_inc(BUILD_SYSTEM, 'version_defaults.mk')

_inc(BUILD_SYSTEM, 'product_config.mk')

# ---------------------------------------------------------------
# Set up configuration for target machine.
# The following must be set:
# 		TARGET_OS = { linux }
# 		TARGET_ARCH = { arm | x86 }

TARGET_ARCH = 'x86'
TARGET_OS = 'linux'
Export('TARGET_ARCH', 'TARGET_OS')
