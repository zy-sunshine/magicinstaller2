from mi.utils.miconfig import MiConfig
def fill_config(config):
    ### fill pre load config items
    CONF = config.LOAD
    CONF.kernelver      = '2.6.35.4'  # The kernel used by installer.
    CONF.distname       = 'MagicLinux'
    CONF.distver        = '3.0'
    CONF.isofn_fmt      = '%s-%s-%d.iso'
    CONF.bootcdfn       = 'MagicLinux-3.0-1.iso'
    CONF.tgtsys_root    = '/tmpfs/tgtsys'
    CONF.distkernelver  = '3.3.0-0.rc3.git6.2mgc30.i686.PAE'
    CONF.kernel_fn      = 'vmlinuz-%s' % CONF.distkernelver
    CONF.initrd_fn      = 'initrd-%s.img' % CONF.distkernelver

    CONF.hotfixdir      = '/tmp/update'

    CONF.BINDIR         = '/usr/bin'
    CONF.DATADIR        = '/usr/share/MagicInstaller'
    
    CONF.DATADIR        = '/usr/share/MagicInstaller'
    
    CONF.LIBDIR         = '/usr/lib/python2.6/site-packages'
    CONF.MODULEDIR      = '/usr/share/MagicInstaller/modules'
    CONF.OPERATIONDIR   = '/usr/share/MagicInstaller/operations'
    CONF.TEXTDOMAIN     = 'magic.installer'

    CONF.PKGTYPE        = 'rpm'

    CONF.full_width     = 800
    CONF.full_height    = 600

    CONF.HELP_WIDTH     = CONF.full_width * 0.6
    CONF.HELP_HEIGHT    = CONF.full_height * 0.9

    CONF.MBRoot         = '/mnt/MagicBooter'

    CONF.dolog         = True

    CONF.useudev       = True

    CONF.fstype_map = {
        # fstype : (mount_type, make_command, minsize(m), maxsize(m), flags)
        # For flags:  b: grub can be installed on the partition which contain
        #                this type of filesystem.
        'ext3':       ('ext3',     '/sbin/mkfs.ext3 -I 128',           1,   -1, 'b'),
        'ext2':       ('ext2',     'internal',                  1,   -1, 'b'),
        'ext4':       ('ext4',     '/sbin/mkfs.ext4',           1,   -1, 'b'),
        'fat32':      ('vfat',     'internal',                  1,   -1, 'b'),
        'fat16':      ('vfat',     'internal',                  1, 2048, 'b'),
        'iso9660':    ('iso9660',  '',                         -1,   -1, ''),
        'jfs':        ('jfs',      '/sbin/mkfs.jfs -q',        16,   -1, 'b'),
        'linux-swap': ('',         'internal',                 -1,   -1, ''),
        #'ntfs':       ('ntfs',      '',                          -1,    -1,  ''),
        'ntfs':       ('ntfs-3g',   '/sbin/mkfs.ntfs -Q',         1,    -1,  ''),
        'reiserfs':   ('reiserfs', '/sbin/mkreiserfs -f -f',   33,   -1, 'b'),
        'xfs':        ('xfs',      '/sbin/mkfs.xfs -q -f',      5,   -1, 'b')
    }

    # Get MagicBooter parameter from mbsave.py
    CONF.EXPERT_MODE = 1
    CONF.RESCUE_MODE = 0
    CONF.TEXT_MODE = 0
    CONF.DEBUG_MODE = 1
    CONF.log_file = '/var/log/mi/mi.log'

    ### fill runtime config items
    CONF = config.RUN
    #--- all_part_infor --------------------------------------------------
    # If 'reprobe_all_disk_required' is set to True, the parted step must reprobe
    # all disks.
    CONF.reprobe_all_disks_required = 0

    # all_part_infor is a map which indexed by device filename, such as '/dev/hda'.
    # Its value is a list. The element of the list is a tuple. Each tuple represent
    # a partition.
    # The tuple is (partnum, parttype, partflag, start, end, format_or_not,
    #               orig_filesystem/format_to_filesystem, mountpoint, not_touched)
    # The all_part_infor is filled by parted module for each leave.
    # It is read by the other modules that run after parted.

    CONF.all_part_infor = {}

    # list of (orig_partdevname, filesystem, new_partdevname)
    CONF.all_orig_part = []

    # root_device: used to store the partition device file name mount on '/'.
    CONF.root_device = None

    # boot_device: used to store the partition device file name which contain '/boot'.
    CONF.boot_device = None

    # swap_device: used to store the partition device file name which used as swap.
    CONF.swap_device = None

    CONF.mount_all_list = []

    CONF.skipxsetting = 0

    CONF.path_tftproot = '/tmpfs/tftpboot'
    
    CONF.pkgarr_probe_status = 0
    
    CONF.win_probe_status = 0

def test_getconf():
    CONF = MiConfig.get_instance()
    CONF.load_from_file('config.ini')
    import pdb; pdb.set_trace()
    CONF.dump()
if __name__ == '__main__':
    if 1:
        CONF = MiConfig.get_instance()
        fill_config(CONF)
        CONF.save_to_file('config.ini')
        #CONF.dump()
    else:
        test_getconf()