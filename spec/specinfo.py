#!/usr/bin/python

### Global information ###

# distname is used to specify the name of the installed distribution.
#
distname='MagicLinux'

# distver is used to specify the version of the installed distribution.
#
distver='2.5'

# distkernelver is used to specify the kernel version which used by the
# installed distribution.
#
distkernelver='2.6.30.10-smp'

# pkgtype is used to specify the package management scheme used by the
# installed distribution. Now only 'rpm' is supported.
#
pkgtype='tar'

# pkgdirs is used to specify the directories which contain the packages
# which should be installed by MagicInstaller as a part of the installed
# distribution. Multiple directories can be separated by ':'. This value
# can be overrided through the command line argument of scons.
#
pkgdirs='spec/packages'

# langset is used to specify the language set supported in installation
# progress. It is a 'colon' separated string.
#
langset='zh_CN:en'


### Information provided for MagicBooter ###

# welcome message is used to show in the first message box for magicbooter
# which should be provided in English only. Note that this string will be
# placed into m4 command and put into C string, so be carefully about '\n'.
#
welcome="Welcome to MagicLinux 2.5 (Jingyou)!"

# kmods_arrange is map which key is the boot/driver floppy disk name and
# the value is the modules which should be placed in. The item with 'boot'
# key specify the modules which should be distributed with boot floppy disk.
# In the module list, module name can be used directly, directory is also
# permitted. And item prefixed with '@' will be added forcely, otherwise
# the modules which are not exists in pcitable will be omitted.
#
# kernel 2.4
# kmods_arrange = {
#    "boot" : [ '@ext3.o', '@jfs.o', '@ntfs.o', '@reiserfs.o', '@vfat.o' ],
#    "scsi" : [ '@xfs.o', '@sd_mod.o', '@kernel/drivers/md', 'kernel/drivers/scsi' ],
#    "net" : ['@xfs.o', '@kernel/drivers/md', 'kernel/drivers/net' ]
# }
# kernel 2.6, fs as module
#kmods_arrange = {
#   "boot" : [ '@ext3', '@jfs', '@ntfs', '@reiserfs', '@vfat' ],
#   "scsi" : [ '@xfs', 'kernel/drivers/scsi' ],
##   "net" : ['@xfs', 'kernel/drivers/net' ]
#}
# kernel 2.6, fs builtin
kmods_arrange = {
   "boot" : [ ],
   "scsi" : [ 'kernel/drivers/scsi' ],
   "net" : ['kernel/drivers/net']
}


### Information about package arrangement ###

######################################################################
# volume_limit_list is used to divide the packages into several media.
# Because one CDROM can't store any data more than 650MB, and the current
# distribution always exceed this limitation, so there should be a way to
# arrange the packages into more then one CDROMs. volume_limit_list list
# the volume limitation for each media in bytes.
#
volume_limit_list = [1300*1024*1024, 640*1024*1024, 640*1024*1024]

######################################################################
# placement_list is used to list the package that must be put in which media.
# For example:
#   [['mktemp-1.5-18.i386.rpm'], ['bash-2.05b-20.i386.rpm'], []]
#   which means 'mktemp' must be put into the first media, 'bash' must be put
#   into the first media or second media. and so on.
#
#placement_list = [[]]

######################################################################
# toplevel_groups is used to create groups for the user convenience.
# toplevel_groups is a map. The key is the map name, the value is the map
# package list. This script will resolve the dependency automatically and
# put it into the output result.
# Note that the key 'lock' has different meaning, the packages in 'lock'
# group will be installed forcely.
# For example:
# { 'lock':  ['bash-2.05b-20.i386.rpm'],
#   'gnome': ['gnome-desktop-2.2.0.1-4.i386.rpm',
#             'gnome-applets-2.2.0-8.i386.rpm',
#             ...]}
#
#toplevel_groups = {}

######################################################################
# add_deps is used to add the lost dependencies.
# add_deps is a map which key is the package and the value is the list of
#   the packages that the package depends.
# For example:
#  { 'libacl1-2.2.4-1.i386.rpm' : ['libattr1-2.2.0-1.i386.rpm'] }
#
#add_deps = {'kernel-2.6.9-5mgc.i686.rpm' : ['mkinitrd-3.5.22-10mgc.i686.rpm'], 'elfutils-0.76-2.i686.rpm' : ['rpm-python-4.3.3-8mgc.i686.rpm']}
#add_deps = {'coreutils-7.0-7mgc25.i686.rpm' : [ 'bash-4.0-1mgc25.i686.rpm' ], 'coreutils-7.0-7mgc25.i686.rpm' : [ 'info-4.13-3mgc25.i686.rpm' ], 'libstdc++-4.4.0-5.i686.rpm' : ['coreutils-7.0-7mgc25.i686.rpm']}

######################################################################
# remove_deps is used to resolve the loop dependencies.
# remove_deps is a map which key is the package and the value is the list of
#   the packages that the package shouldn't remove depends.
# For example:
#  { 'pam-0.75-49.i386.rpm' : ['initscripts-7.14-9.i386.rpm'] }
#

# Omit it, if use 1 it will work, notice the indent is 4 spaces.
if 0:
    remove_deps = {
    'coreutils-7.0-7mgc25.i686.rpm':
        ['util-linux-ng-2.17.2-2mgc25.i686.rpm',
         'libcap-2.16-1mgc25.i686.rpm',
         'gmp-4.2.4-2mgc25.i686.rpm',
         'ncurses-5.7-2.20090207mgc25.i686.rpm',
         'grep-2.5.3-2mgc25.i686.rpm',
         'pam-1.1.0-2mgc25.i686.rpm',
         'libacl-2.2.47-2mgc25.i686.rpm',
         'info-4.13-3mgc25.i686.rpm',
         'libattr-2.4.43-2mgc25.i686.rpm',
        ],
    'glibc-2.10.1-2mgc25.i686.rpm':
        ['glibc-common-2.10.1-2mgc25.i686.rpm',
         'basesystem-25-1mgc25.noarch.rpm',
         'libgcc-4.4.0-5.i686.rpm',
         'nss-softokn-freebl-3.12.4-1mgc25.i686.rpm',
        ],
    'binutils-2.19.51.0.2-1mgc25.i686.rpm':
        ['info-4.13-3mgc25.i686.rpm',
         'bash-4.0-1mgc25.i686.rpm',
         'zlib-1.2.3-19mgc25.i686.rpm',
         'glibc-2.10.1-2mgc25.i686.rpm',
        ],
    'bash-4.0-1mgc25.i686.rpm':
        ['ncurses-libs-5.7-2.20090207mgc25.i686.rpm',
        ],
    }

# For the detail to deal with loop dependencies between packages, refer to
# the comments and code in scripts/PkgArrange.py.


######################################################################
# basepkg_list is a list content the base tool chain packages order by the
# dependency. MI will put packages in order refer to this list.

basepkg_list = ['binutils',
                #'binutils-devel',
                #'kernel-headers',
                'glibc',
                #'glibc-common',
                #'glibc-devel',
                #'glibc-headers',
                #'glibc-static',
                #'glibc-utils',
                'bash',
                #'bash-completion',
                'coreutils',
             ]

######################################################################
# autopart_profile is used to add the auto-partition
# profile. autopart_profile is a map which key is the profile and the
# value is the description and partition definitions.
#
# Note that the profile name is used as a XML tag, so please use just
# letters and numbers. The description will be used to shown in a
# selection box, and translation is available by updating po files.
#
# The part tuple is a form of ("mountpoint", "filesystem", "size")

#  - mountpoint can be the mount path of the partitionn or "SWAP" as a
#  swap partition.

#  - filesystem can be one of "ext2", "ext3", "reiserfs", "fat16",
#  "fat32", "jfs", "xfs".
#
#  - size can be size of "64M", "15G", or percents like "50%",
#  "30%". If there's any percents size, the allocation is different,
#  the percents are served as a proportion. For example: the free
#  space is 12G, there're three percents partitions (10%, 90%, 20%)
#  left, so there respective allocated size will be
#  12G*10/(10+90+20) = 1G, 12G*90/(10+90+20)=9G, 12G*20/(10+90+20)=2G.

# For exammple:
# autopart_profile = {
#     'default' : ["Separated /boot, /, /home",
#                  ("/boot", "ext2", "64M"),
#                  ("/", "ext3", "5G"),
#                  ("/home", "ext3", "100%")],
#     'custom' :  ["Customed autopart profile",
#                  ("SWAP", "SWAP", "15G"),
#                  ("/", "ext3", "15G"),
#                  ("/usr/local", "ext3", "15G"),
#                  ("/tmp", "ext3", "15G"),
#                  ("/home", "ext3", "100%")]
#     }
autopart_profile = {
    'default' : ["Single partition with swap",
                 ("SWAP", "SWAP", "512M"),
                 ("/", "ext3", "100%")], 

#    'common' : ["Separated /boot, /, /home",
#                 ("/boot", "ext2", "64M"),
#                 ("/", "ext3", "2000M"),
#                 ("/home", "ext3", "0")],

    'common' : ["Separated /, /home",
                 ("/", "ext3", "5160M"),
                 ("/home", "ext3", "2060M")],

    'custom' :  ["Customed autopart profile",
                 ("SWAP", "SWAP", "512M"),
                 ("/", "ext3", "2060M"),
                 ("/usr", "ext3", "4130M"),
                 ("/home", "ext3", "2060M")]
    }
