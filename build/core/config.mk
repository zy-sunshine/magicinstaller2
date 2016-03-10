# set up stdard variables
import os
Import('TOPDIR', 'BUILD_SYSTEM', '_p', '_inc', '_error')

SRC_TARGET_DIR=_p(TOPDIR, 'build/target')
PLATFORM_VERSION='2.0.1'
Export('SRC_TARGET_DIR', 'PLATFORM_VERSION')

_inc(BUILD_SYSTEM, 'envsetup.mk')

### Because we are Linux Distribution, so we not aim at one device, remove BoardConfig.mk
##
# Import('TARGET_DEVICE') # envsetup -> product_config -> _get_var_by_product, get it from every MiProduct.mk(identify by TARGET_PRODUCT)

# # Boards may be defined under $(SRC_TARGET_DIR)/board/$(TARGET_DEVICE)
# # or under vendor/*/$(TARGET_DEVICE).  Search in both places, but
# # make sure only one exists.
# # Real boards should always be associated with an OEM vendor.
# def wildcard(*args):
#     import glob
#     retlst = []
#     for arg in args:
#         p = glob.glob(arg)
#         if p and os.path.exists(p[0]):
#             retlst.append(p[0])
#     return retlst

# board_config_mk = wildcard("%(SRC_TARGET_DIR)s/board/%(TARGET_DEVICE)s/BoardConfig.mk" % {'TARGET_DEVICE': TARGET_DEVICE, 'SRC_TARGET_DIR': SRC_TARGET_DIR},
#         "%(TOPDIR)s/device/*/%(TARGET_DEVICE)s/BoardConfig.mk" % {'TARGET_DEVICE': TARGET_DEVICE, 'TOPDIR': TOPDIR},
#         "%(TOPDIR)s/vendor/*/%(TARGET_DEVICE)s/BoardConfig.mk" % {'TARGET_DEVICE': TARGET_DEVICE, 'TOPDIR': TOPDIR})
# if not board_config_mk:
#     _error('No config file found for TARGET_DEVICE %(TARGET_DEVICE)s' % {'TARGET_DEVICE': TARGET_DEVICE})

# if len(board_config_mk) > 1:
#     _error('Multiple board config files for TARGET_DEVICE %(TARGET_DEVICE)s: %(board_config_mk)s' % 
#         {'TARGET_DEVICE': TARGET_DEVICE, 'board_config_mk': board_config_mk})

# board_config_mk = board_config_mk[0]

# _inc(board_config_mk)
# TARGET_DEVICE_DIR = os.path.dirname(board_config_mk)

_inc(BUILD_SYSTEM, 'dumpvar.mk')

