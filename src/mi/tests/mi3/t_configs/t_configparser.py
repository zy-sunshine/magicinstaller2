import ConfigParser

config = ConfigParser.RawConfigParser()

# When adding sections or items, add them in the reverse order of
# how you want them to be displayed in the actual file.
# In addition, please note that using RawConfigParser's and the raw
# mode of ConfigParser's respective set functions, you can assign
# non-string values to keys internally, but will receive an error
# when attempting to write to a file or when you get it in non-raw
# mode. SafeConfigParser does not allow such assignments to take place.
config.add_section('Section1')
config.set('Section1', 'int', '15')
config.set('Section1', 'bool', 'true')
config.set('Section1', 'float', '3.1415')
config.set('Section1', 'baz', 'fun')
config.set('Section1', 'bar', 'Python')
config.set('Section1', 'foo', '%(bar)s is %(baz)s!')
config.add_section('Section2')
config.set('Section2', 'dict', {'a': 1, 'b': 2, 'cc': 'dd'})
config.set('Section2', 'list', [2,3,4,5,6,7])
config.set('Section2', 'part',{
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
    })

# Writing our configuration file to 'example.cfg'
with open('example.cfg', 'wb') as configfile:
    config.write(configfile)