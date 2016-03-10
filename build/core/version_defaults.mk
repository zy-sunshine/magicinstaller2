# Guarantees that the following are defined:
#     PLATFORM_VERSION
#     PLATFORM_SDK_VERSION
#     PLATFORM_VERSION_CODENAME
#     DEFAULT_APP_TARGET_SDK
#     BUILD_ID
#     BUILD_NUMBER


# BUILD_ID
# Used to signify special builds.  E.g., branches and/or releases,
# like "M5-RC7".  Can be an arbitrary string, but must be a single
# word and a valid file name.

# BUILD_ID = "ML-rc1"

# Export('BUILD_ID')
