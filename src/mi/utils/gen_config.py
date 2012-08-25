import os
from mi.utils.miconfig import MiConfig
def fill_config(config):
    ### fill pre load config items
    CONF = config.LOAD
    CONF.CONF_OPERATIONDIR = '/usr/share/MagicInstaller/operations'
    CONF.CONF_EXPERT_MODE = 1

    CONF.CONF_HELP_WIDTH = 480.0
    CONF.CONF_HELP_HEIGHT = 540.0

    CONF.CONF_INITRD_FN = 'initrd-3.4.4-1mgc30.i686.PAE.img'

    CONF.CONF_FULL_WIDTH = 800
    CONF.CONF_FULL_HEIGHT = 600

    CONF.CONF_KERNEL_FN = 'vmlinuz-3.4.4-1mgc30.i686.PAE'
    CONF.CONF_DISTKERNELVER = '3.4.4-1mgc30.i686.PAE'
    CONF.CONF_KERNELVER = '2.6.35.4'
    CONF.CONF_DISTVER = '3.0'

    CONF.CONF_MBROOT = '/mnt/MagicBooter'
    CONF.CONF_RESCUE_MODE = 0
    CONF.CONF_LIBDIR = '/usr/lib/python2.6/site-packages'
    #CONF.CONF_DATADIR = '/usr/share/MagicInstaller'
    CONF.CONF_DATADIR = '/home/zhangyang09/work/magicinstaller2/src/mi'
    CONF.CONF_USEUDEV = True
    CONF.CONF_TEXT_MODE = 0
    CONF.CONF_FSTYPE_MAP = {'iso9660': ('iso9660', '', -1, -1, ''), 'fat32': ('vfat', 'internal', 1, -1, 'b'), 'linux-swap': ('', 'internal', -1, -1, ''), 'ntfs': ('ntfs-3g', '/sbin/mkfs.ntfs -Q', 1, -1, ''), 'reiserfs': ('reiserfs', '/sbin/mkreiserfs -f -f', 33, -1, 'b'), 'xfs': ('xfs', '/sbin/mkfs.xfs -q -f', 5, -1, 'b'), 'ext4': ('ext4', '/sbin/mkfs.ext4', 1, -1, 'b'), 'ext3': ('ext3', '/sbin/mkfs.ext3 -I 128', 1, -1, 'b'), 'ext2': ('ext2', 'internal', 1, -1, 'b'), 'fat16': ('vfat', 'internal', 1, 2048, 'b'), 'jfs': ('jfs', '/sbin/mkfs.jfs -q', 16, -1, 'b')}
    CONF.CONF_BINDIR = '/usr/bin'
    CONF.CONF_TGTSYS_ROOT = '/tmpfs/tgtsys'
    CONF.CONF_MNT_ROOT = '/tmpfs/mnt'
    CONF.CONF_PKGARR_FILE = "pkgarr.py"
    
    CONF.CONF_PKGARR_SER_CDPATH = ['%s/base' % CONF.CONF_DISTNAME]
    CONF.CONF_PKGARR_SER_HDPATH = ['boot', CONF.CONF_DISTNAME, 'usr/share/MagicInstaller', '', 'tmp']
    CONF.CONF_ISOLOOP = 'loop3'  # Use the last loop device to mount iso files.
    
    CONF.CONF_PKGTYPE = 'rpm'
    CONF.CONF_BOOTCDFN = 'MagicLinux-3.0-1.iso'     #### the first iso is the boot iso, it has grub and pkgarr.py
    CONF.CONF_ISOFN_FMT = '%s-%s-%d.iso'
    CONF.CONF_DEBUG_MODE = 1
    CONF.CONF_DOLOG = True
    CONF.CONF_DISTNAME = 'MagicLinux'
    CONF.CONF_MODULEDIR = '/usr/share/MagicInstaller/modules'
    CONF.CONF_TEXTDOMAIN = 'magic.installer'
    CONF.CONF_HOTFIXDIR = '/tmp/update'
    CONF.CONF_LOG_FILE = '/var/log/mi/mi.log'
    
    ### fill runtime config items
    CONF = config.RUN
    #--- all_part_infor --------------------------------------------------
    # If 'reprobe_all_disk_required' is set to True, the parted step must reprobe
    # all disks.
    CONF.g_reprobe_all_disks_required = 0

    # all_part_infor is a map which indexed by device filename, such as '/dev/hda'.
    # Its value is a list. The element of the list is a tuple. Each tuple represent
    # a partition.
    # The tuple is (partnum, parttype, partflag, start, end, format_or_not,
    #               orig_filesystem/format_to_filesystem, mountpoint, not_touched)
    # The all_part_infor is filled by parted module for each leave.
    # It is read by the other modules that run after parted.

    CONF.g_all_part_infor = {}

    # list of (orig_partdevname, filesystem, new_partdevname)
    CONF.g_all_orig_part = []

    # root_device: used to store the partition device file name mount on '/'.
    CONF.g_root_device = None

    # boot_device: used to store the partition device file name which contain '/boot'.
    CONF.g_boot_device = None

    # swap_device: used to store the partition device file name which used as swap.
    CONF.g_swap_device = None

    CONF.g_mount_all_list = []

    CONF.g_skipxsetting = 0

    CONF.g_path_tftproot = '/tmpfs/tftpboot'
    
    CONF.g_pkgarr_probe_status = 0
    
    CONF.g_win_probe_status = 0

    CONF.g_fstype_map = {}
    CONF.g_fstype_swap_index = -1
    CONF.g_win_probe_result = []
    CONF.g_pkgarr_probe_result = []

    CONF.g_path_allpa = os.path.join(CONF.g_path_tftproot, 'allpa')
    CONF.g_choosed_patuple = []
    CONF.g_arch_map = {}
    CONF.g_arrangement = []
    CONF.g_archsize_map = {}
    CONF.g_pkgpos_map = {}
    CONF.g_toplevelgrp_map = {}

def test_getconf():
    CONF = MiConfig.get_instance()
    CONF.load_from_file('config.json')
    import pdb; pdb.set_trace()
    CONF.dump()
    
if __name__ == '__main__':
    if 1:
        CONF = MiConfig.get_instance()
        fill_config(CONF)
        CONF.save_to_file('config.json')
        #CONF.dump()
    else:
        test_getconf()