#!/usr/bin/python
#encoding=utf8

from gettext import gettext as _
import iconv
import sys
import getdev
import parted
import _ped
import isys

# Because the short operation and long operation are run in different process,
# they can't share the parted results. So all operations except status-free
# operation have to be 'long' even if it can terminate immediately.

from miutils.miconfig import MiConfig
CONF = MiConfig.get_instance()
CONF_USEUDEV = CONF.LOAD.CONF_USEUDEV
CONF_FSTYPE_MAP = CONF.LOAD.CONF_FSTYPE_MAP
CONF_TGTSYS_ROOT = CONF.LOAD.CONF_TGTSYS_ROOT

from miutils.miregister import MiRegister
register = MiRegister()

from miutils.milogger import get_long_dolog
dolog = get_long_dolog(__name__).w

# Status-free operations.
@register.server_handler('short')
def all_file_system_type():
    fs_list = []
    #fs = parted.file_system_type_get_next()
    #while fs:
    #    if fs_map.has_key(fs.name):
    #        fs_list.append(fs.name)
    #    fs = parted.file_system_type_get_next(fs)
    fs_map = parted.fileSystemType
    fs_list = fs_map.keys()
    if 'linux-swap' not in fs_list:
        fs_list.append('linux-swap')
    return  fs_list

@register.server_handler('short')
def all_disk_type():
    dtype_list = []
    #dtype = parted.disk_type_get_next()
    #while dtype:
    #    dtype_list.append(dtype.name)
    #    dtype = parted.disk_type_get_next(dtype)
    dtype_map = parted.diskType
    dtype_list = dtype_map.keys()
    return  dtype_list
    
#-------------------- long operations ---------------------------
# Status globals

parted_MIN_FREESPACE = 2048  # 1M
all_harddisks = {}

# Status-Related operations.

@register.server_handler('long')
def revision_fstype(fstype):
    ''' revise the file system version between MI and to libparted, current only linux-swap version '''
    if fstype == 'linux-swap':
        fstype = 'linux-swap(v0)'
    return fstype
    
@register.server_handler('long')
def device_probe_all(mia, operid, dummy):

    def get_device_list():
        hd_list = filter(lambda d: d.type != parted.DEVICE_DM, parted.getAllDevices())
        
        return hd_list

    global all_harddisks
    mia.set_step(operid, 0, -1)
    result = []
    # The following commented code is implemented by kudzu.
    devlist = get_device_list()
    if devlist:
        for dev in devlist:
            newdisklabel = None
            try:
                disk = parted.Disk(dev)
            except _ped.DiskLabelException:
                # For the disk without any disk label, create it.
                # disk label is disk partition table format
                dltype = parted.diskType['msdos']
                disk = parted.freshDisk(device=dev, ty=dltype)
                #newdisklabel = 'y'
                #disk = dev.disk_new_fresh(parted.disk_type_get('msdos'))
            # Model might contain GB2312, it must be convert to Unicode.
            model = iconv.iconv('gb2312', 'utf8', dev.model).encode('utf8')
            result.append((dev.path, dev.length, model))
            all_harddisks[dev.path] = (dev, disk, newdisklabel)
    #dolog('operations.parted.device_probe_all: %s\n' % str(result))
    return  result

@register.server_handler('long')
def get_all_partitions(mia, operid, devpath):
    def part2result(part):
        flags = []
        avaflags = []
        label = 'N/A'
        if part.active:
            for f in parted.partitionFlag.keys():
                if part.isFlagAvailable(f):
                    avaflags.append(f)
                    if part.getFlag(f):
                        flags.append(f)
            if disk.supportsFeature(parted.DISK_TYPE_PARTITION_NAME):
                label = part.name

        if part.fileSystem:    
            fs_type_name = part.fileSystem.type
        else:
            fs_type_name = 'N/A'
        #if part.is_active() != 0:
        #    for f in range(parted.PARTITION_FIRST_FLAG,
        #                   parted.PARTITION_LAST_FLAG + 1):
        #        if part.is_flag_available(f):
        #            avaflags.append(f)
        #            if part.get_flag(f):
        #                flags.append(f)
        #    if part.disk.type.check_feature(parted.DISK_TYPE_PARTITION_NAME):
        #        label = part.get_name()
        #if part.fs_type:
        #    fs_type_name = part.fs_type.name
        #else:
        #    fs_type_name = 'N/A'
        
        return (part.number, flags, part.type, part.geometry.length,
                fs_type_name, label, part.geometry.start, part.geometry.end, avaflags)

    result = []
    if all_harddisks.has_key(devpath):
        disk = all_harddisks[devpath][1]
        if disk:
            part = disk.getFirstPartition()
            while part:
                if part.type & parted.PARTITION_METADATA == 0:
                    result.append(part2result(part))
                part = part.nextPartition()
            # Another way to get all partitions, but not include freespace partitions.
            #for part in disk.partitions:
            #    result.append(part2result(part))
                
            #part = disk.next_partition()
            #while part:
            #    if part.type & parted.PARTITION_METADATA == 0:
            #        result.append(part2result(part))
            #    part = disk.next_partition(part)
    #dolog('operations.parted.get_all_partitions: %s\n' % str(result))
    return  result

@register.server_handler('long')
def get_disk_type(mia, operid, devpath):
    if all_harddisks.has_key(devpath):
        disk = all_harddisks[devpath][1]
        if disk:
            if disk.supportsFeature(parted.DISK_TYPE_PARTITION_NAME):
                support_partition_name = 'true'
            else:
                support_partition_name = 'false'
            return (disk.type, support_partition_name)
        #if disk:
        #    if disk.type.check_feature(parted.DISK_TYPE_PARTITION_NAME):
        #        support_partition_name = 'true'
        #    else:
        #        support_partition_name = 'false'
        #    return (disk.type.name, support_partition_name)
    return  ('N/A', 'false')

def _get_left_bound(sector, disk):
    #under_sector = disk.get_partition_by_sector(sector)
    under_sector = disk.getPartitionBySector(sector)
    if not under_sector:
        return  sector
    if under_sector.type & parted.PARTITION_FREESPACE:
        return  under_sector.geometry.start
    else:
        return  sector

def _get_right_bound(sector, disk):
    # disk.getPartitionBySector.__doc__
    # Returns the Partition that contains the sector.  If the sector
    #   lies within a logical partition, then the logical partition is
    #   returned (not the extended partition).
    #under_sector = disk.get_partition_by_sector(sector)
    under_sector = disk.getPartitionBySector(sector)
    if not under_sector:
        return  sector
    if under_sector.type & parted.PARTITION_FREESPACE:
        return  under_sector.geometry.end
    else:
        return  sector

#def _grow_over_small_freespace(geometry, disk):
#    if geometry.length < parted_MIN_FREESPACE * 5:
#        return  geometry
#    start = _get_left_bound(geometry.start, disk)
#    if start >= geometry.end:
#        return  None
#    if geometry.start - start < parted_MIN_FREESPACE:
#        geometry.set_start(start)
#    end = _get_right_bound(geometry.end, disk)
#    if end <= geometry.start:
#        return  None
#    if end - geometry.end < parted_MIN_FREESPACE:
#        geometry.set_end(end)
#    return  geometry
    
def _grow_over_small_freespace(start_in, end_in, disk):
    length_in = end_in - start_in + 1
    start_out = start_in
    end_out = end_in
    length_out = length_in
    
    if length_in < parted_MIN_FREESPACE * 5:
        return  (start_out, end_out, length_out)
    start = _get_left_bound(start_in, disk)
    if start >= end_in:
        return  None
    if start_in - start < parted_MIN_FREESPACE:
        start_out = start
    end = _get_right_bound(end_in, disk)
    if end <= start_in:
        return  None
    if end - end_in < parted_MIN_FREESPACE:
        end_out = end
    length_out = end_out - start_out + 1
    return (start_out, end_out, length_out)

@register.server_handler('long')
def add_partition(mia, operid, devpath, parttype, fstype, start, end):
    fstype = revision_fstype(fstype)
    if all_harddisks.has_key(devpath):
        (dev, disk, dirty_or_not) = all_harddisks[devpath]
        if disk:
            #constraint = dev.constraint_any()
            constraint = parted.Constraint(device=dev)#exactGeom=newgeom)
            if parttype == 'primary':
                parttype = 0
            elif parttype == 'extended':
                parttype = parted.PARTITION_EXTENDED
            elif parttype == 'logical':
                parttype = parted.PARTITION_LOGICAL
            if fstype != 'N/A':
                #fstype = parted.file_system_type_get(fstype)
                fstype = parted.fileSystemType[fstype]
            else:
                fstype = None
            try:
                #newpart = disk.partition_new(parttype, fstype, start, end)
                newgeom_bound = _grow_over_small_freespace(start, end, disk)
                if not newgeom_bound:
                    return (-1, "Can't get the geometry of new partition (start=%s end=%s)." % (start, end))
                newgeom = parted.Geometry(device=dev, start=newgeom_bound[0], end=newgeom_bound[1])
                # We can use _ped's geometry to build parted's Geometry
                #newgeom = parted.Geometry(PedGeometry=newpart.geometry.getPedGeometry())
                if newgeom:
                    newpart = parted.Partition(disk=disk, type=parttype, geometry=newgeom)
                    disk.addPartition(partition=newpart, constraint=constraint)
                    if fstype:
                        newpart.getPedPartition().set_system(fstype)
                #newgeom = _grow_over_small_freespace(newpart.geometry, disk)
                #if newgeom:
                #    newpart.geom.set_start(newgeom.start)
                #    newpart.geom.set_end(newgeom.end)
                #    disk.add_partition(newpart, constraint)
                #    if fstype:
                #        newpart.set_system(fstype)
                
            #except  parted.error:
            #    exc_info = sys.exc_info()
            #    return (-1, str(exc_info[1]))
            except _ped.PartitionException, errmsg:
                return(-1, str(errmsg))
            all_harddisks[devpath] = (dev, disk, 'y')
            return (newpart.geometry.start, '')
    return (-1, _("Can't find the specified disk."))

@register.server_handler('long')
def set_flags_and_label(mia, operid, devpath, part_start,
                        true_flags, false_flags, set_label, label):
    if all_harddisks.has_key(devpath):
        disk = all_harddisks[devpath][1]
        if disk:
            part = disk.getFirstPartition()
            while part:
                if part.geometry.start == part_start:
                    for tf in true_flags:
                        part.setFlag(tf)
                    for ff in false_flags:
                        part.unsetFlag(ff)
                    if set_label == 'true':
                        part.getPedPartition().set_name(label)
                    break
                part = part.nextPartition()

            #part = disk.next_partition()
            #while part:
            #    if part.geom.start == part_start:
            #        for tf in true_flags:
            #            part.set_flag(tf, 1)
            #        for ff in false_flags:
            #            part.set_flag(ff, 0)
            #        if set_label == 'true':
            #            part.set_name(label)
            #        break
            #    part = disk.next_partition(part)
            all_harddisks[devpath] = (all_harddisks[devpath][0], disk, 'y')
    return  0

@register.server_handler('long')
def delete_partition(mia, operid, devpath, part_start):
    if all_harddisks.has_key(devpath):
        disk  = all_harddisks[devpath][1]
        if disk:
            part = disk.getFirstPartition()
            while part:
                if part.geometry.start == part_start:
                    #disk.delete_partitons(part)
                    disk.removePartition(part)
                    break
                part = part.nextPartition()
            all_harddisks[devpath] = (all_harddisks[devpath][0], disk, 'y')
        #if disk:
        #    part = disk.next_partition()
        #    while part:
        #        if part.geom.start == part_start:
        #            disk.delete_partition(part)
        #            break
        #        part = disk.next_partition(part)
        #    all_harddisks[devpath] = (all_harddisks[devpath][0], disk, 'y')
    return get_all_partitions(mia, operid, devpath)

@register.server_handler('long')
def reload_partition_table(mia, operid, devpath):
    if all_harddisks.has_key(devpath):
        dev = all_harddisks[devpath][0]
        try:
            all_harddisks[devpath] = (dev, parted.Disk(dev), None)
        except _ped.DiskLabelException:
            dltype = parted.diskType['msdos']
            all_harddisks[devpath] = (dev, parted.freshDisk(device=dev, ty=dltype), 'y')
        #try:
        #    all_harddisks[devpath] = (dev, parted.PedDisk.new(dev), None)
        #except parted.error:
        #    dltype = parted.disk_type_get('msdos')
        #    all_harddisks[devpath] = (dev, dev.disk_new_fresh(dltype), 'y')
    return 0

@register.server_handler('long')
def disk_new_fresh(mia, operid, devpath, dltype):
    #dltype = parted.disk_type_get(dltype)
    dltype = parted.diskType[dltype]
    if dltype and all_harddisks.has_key(devpath):
        dev = all_harddisks[devpath][0]
        #all_harddisks[devpath] = (dev, dev.disk_new_fresh(dltype), 'y')
        all_harddisks[devpath] = (dev, parted.freshDisk(device=dev, ty=dltype), 'y')
    return 0

@register.server_handler('long')
def get_all_dirty_disk(mia, operid, dummy):
    mia.set_step(operid, 0, -1)
    result = []
    for devpath in all_harddisks.keys():
        if all_harddisks[devpath][2]:
            result.append(devpath)
    return  result

@register.server_handler('long')
def commit_devpath(mia, operid, devpath):
    mia.set_step(operid, 0, -1)
    if all_harddisks.has_key(devpath):
        disk  = all_harddisks[devpath][1]
        if disk:
            try:
                disk.commit()
                all_harddisks[devpath] = (all_harddisks[devpath][0], disk, None)
            #except parted.error, errmsg:
            except parted.DiskException as errmsg:
                return  str(errmsg)
    return  0

@register.server_handler('long')
def format_partition(mia, operid, devpath, part_start, fstype):
    mia.set_step(operid, 0, -1)
    if not CONF_FSTYPE_MAP.has_key(fstype):
        errmsg = _('Unrecoginzed filesystem %s.')
        return errmsg % fstype
    if CONF_FSTYPE_MAP[fstype][1] == '':
        errmsg = _('Format %s is not supported.')
        return errmsg % fstype
    if not all_harddisks.has_key(devpath):
        return _('No such device: ') + devpath
    disk = all_harddisks[devpath][1]
    if not disk:
        return _('Not any partition table found on: ') + devpath
    #part = disk.next_partition()
    part = disk.getFirstPartition()
    while part:
        if part.geometry.start != part_start:
            #part = disk.next_partition(part)
            part = part.nextPartition()
            continue
        if CONF_FSTYPE_MAP[fstype][1] == 'internal':
            parted_fstype = parted.fileSystemType[revision_fstype(fstype)]
            try:
                part.getPedPartition().set_system(parted_fstype)
                part.fileSystem.create()
                disk.commit()
                return  0
            except NotImplementedError, errmsg:
                return  str(errmsg)
            except parted.DiskException as errmsg:
                return  str(errmsg)
        else:
            parted_fstype = parted.fileSystemType[revision_fstype(fstype)]
            try:
                part.getPedPartition().set_system(parted_fstype)
                disk.commit()
            except NotImplementedError, errmsg:
                return  str(errmsg)
            except parted.DiskException as errmsg:
                return  str(errmsg)
                
            # Wait for device block appear.
            fblk = False
            trycnt = 0
            # We attemp to detect device file whether exists
            for t in range(5):
                devn = '%s%d' % (devpath, part.number)
                # os.path.exists cannot detect file exists real time
                #if os.path.exists(devn):
                if os.system('ls %s' % devn) == 0:
                    fblk = True
                    break
                else:
                    trycnt += 1
                    time.sleep(1)
                    
            if not fblk:
                return _('Not exists device block on %s: \ntry time: %d\n') % (devpath, trycnt)
                
            #cmd = '%s %s%d' % (CONF_FSTYPE_MAP[fstype][1], devpath, part.number)
            #ret = os.system(cmd)
            #if ret != 0:
            #    errmsg = _('Run "%s" failed: %s\n')
            #    return  errmsg % (cmd, str(ret))
            #else:
            #    return  0
            # Run command to format partition
            cmd_format = CONF_FSTYPE_MAP[fstype][1]
            cmd_f_list = cmd_format.split()
            cmd = cmd_f_list[0]
            argv = cmd_f_list[1:]
            argv.append('%s%d' % (devpath, part.number))
            cmdres = run_bash(cmd, argv)
            dolog('%s %s\n' % (cmd, ' '.join(argv)))
            dolog(' '.join(cmdres['out'])+'\n')
            if cmdres['ret'] != 0:
                errmsg = _('Run "%s %s" failed: %s\ntry time: %d\n')
                return  errmsg % ( cmd, ' '.join(argv), str(cmdres['err']), trycnt )
            else:
                return  0
    return _('Not any partition found on position: ') + str(part_start)

def _gen_fstab(mount_all_list):
    # Generate fstab.
    mountmap = {}
    for (mntdir, devfn, fstype) in mount_all_list:
        if fstype == 'linux-swap':  continue
        if fstype in ('fat32', 'fat16'):
            mountmap[mntdir] = (devfn, CONF_FSTYPE_MAP[fstype][0],
                                'iocharset=cp936,umask=0,defaults', 0, 0)
        elif mntdir == '/':
            mountmap[mntdir] = (devfn, CONF_FSTYPE_MAP[fstype][0],
                                'defaults', 1, 1)
        else:
            mountmap[mntdir] = (devfn, CONF_FSTYPE_MAP[fstype][0],
                                'defaults', 0, 0)
    mountmap['/dev/pts'] = ('none', 'devpts', 'gid=5,mode=620', 0, 0)
    mountmap['/proc']    = ('none', 'proc', 'defaults', 0, 0)
    mountmap['/sys']     = ('none', 'sysfs', 'defaults', 0, 0)
    mountmap['/dev/shm'] = ('none', 'tmpfs', 'defaults', 0, 0)
    #
    #fdlist = kudzu.probe(kudzu.CLASS_FLOPPY,
    #                     kudzu.BUS_IDE | kudzu.BUS_SCSI | kudzu.BUS_MISC,
    #                     kudzu.PROBE_ALL)
    fdlist = getdev.probe(getdev.CLASS_FLOPPY)
    #cdlist = kudzu.probe(kudzu.CLASS_CDROM,
    #                     kudzu.BUS_IDE | kudzu.BUS_SCSI | kudzu.BUS_MISC,
    #                     kudzu.PROBE_ALL)
    cdlist = getdev.probe(getdev.CLASS_CDROM)
    for fd in fdlist:
        mntdir = string.replace(fd.device, 'fd', '/media/floppy')
        if mntdir == '/media/floppy0':  mntdir = '/media/floppy'
        mountmap[mntdir] = (os.path.join('/dev', fd.device),
                            #'auto', 'iocharset=cp936,noauto,user,kudzu,rw,exec,sync', 0, 0)
                            'auto', 'iocharset=cp936,noauto,user,rw,exec,sync', 0, 0)
        os.system('mkdir -p %s' % os.path.join(CONF_TGTSYS_ROOT, mntdir[1:]))
    #if cdlist != []:
    if 0: # remove cdrom entries
        cddevlist = map(lambda cd: cd.device, cdlist)
        cddevlist.sort()
        for cnt in range(len(cddevlist)):
            if cnt == 0:
                mntdir = '/mnt/cdrom'
            else:
                mntdir = '/mnt/cdrom%d' % cnt
            mountmap[mntdir] = (os.path.join('/dev', cddevlist[cnt]),
                                #'iso9660,udf', 'iocharset=cp936,noauto,user,kudzu,ro,exec', 0, 0)
                                'iso9660,udf', 'iocharset=cp936,noauto,user,ro,exec', 0, 0)
            devdir = os.path.join(CONF_TGTSYS_ROOT, 'dev')
            os.system('mkdir -p %s' % devdir)
            os.system('ln -s %s %s' % \
                      (cddevlist[cnt],
                       os.path.join(devdir,
                                    os.path.basename(mntdir))))
            os.system('mkdir -p %s' % os.path.join(CONF_TGTSYS_ROOT, mntdir[1:]))
            cnt = cnt + 1
    etcpath = os.path.join(CONF_TGTSYS_ROOT, 'etc')
    if not os.path.isdir(etcpath):
        os.makedirs(etcpath)
    try:
        fstab = file(os.path.join(etcpath, 'fstab'), 'w')
        fstab.write('#%-14s\t%-23s\t%-15s\t%-15s\t%s %s\n' % \
                    ('device', 'mountpoint', 'filesystem', 'options', \
                         'dump', 'checkpassno'))
        mdkeys = mountmap.keys()
        mdkeys.sort()
        for mntdir in mdkeys:
            (dev, fstype, opts, v1, v2) = mountmap[mntdir]
            fstab.write('%-15s\t%-23s\t%-15s\t%-15s\t%d    %d\n' % \
                        (dev, mntdir, fstype, opts, v1, v2))
        for (mntdir, devfn, fstype) in mount_all_list:
            if fstype == 'linux-swap':
                fstab.write('%-15s\t%-23s\t%-15s\t%-15s\t%d    %d\n' % \
                            (devfn, 'swap', 'swap', 'defaults', 0, 0))
        fstab.close()
    except Exception, errmsg:
        dolog('Generate fstab failed: %s\n' % str(errmsg))

@register.server_handler('long')
def mount_all_tgtpart(mia, operid, mount_all_list, firstcall):
    errmsg = ''
    if os.path.exists('/tmpfs/debug/nomnttgt'):
        dolog('TURN ON: nomnttgt\n')
    else:
        # Mount all target partition as the user will.
        cnt = 0
        mia.set_step(operid, cnt, len(mount_all_list))
        for (mntpoint, devfn, fstype) in mount_all_list:
            if fstype == 'linux-swap':
                if firstcall:
                    try:
                        isys.swapon(devfn)
                    except SystemError, em:
                        errmsg = _('swapon(%s) failed: %s')
                        errmsg = errmsg % (devfn, str(em))
                        # If reach there, we donnot return, continue remaining operations, to avoid cannot generate fstab case.
                        #return  errmsg
            else:
                # Wait for device block appear.
                fblk = False
                trycnt = 0
                for t in range(5):
                    if os.system('ls %s' % devfn) == 0:
                        fblk = True
                        break
                    else:
                        trycnt += 1
                        time.sleep(1)
                    
                if not fblk:
                    return _('Not exists device block on %s: \ntry time: %d\n') % (devfn, trycnt)

                realpath = os.path.join(CONF_TGTSYS_ROOT, mntpoint[1:])
                ret, mntdir = mount_dev(CONF_FSTYPE_MAP[fstype][0], devfn, realpath)
                if not ret:
                    errmsg = _('Mount %s on %s as %s failed: %s')
                    errmsg = errmsg % (devfn, realpath, fstype, mntdir)
                    #return  errmsg
            cnt = cnt + 1
            mia.set_step(operid, cnt, len(mount_all_list))
    # Mount /proc.
    procpath = os.path.join(CONF_TGTSYS_ROOT, 'proc')
    if not os.path.isdir(procpath):
        os.makedirs(procpath)
    if not os.path.exists(os.path.join(procpath, 'cmdline')):
        #isys.mount('proc', 'proc', procpath)
        ret, msg = mount_dev('proc', 'proc', mntdir=procpath)
    # Mount /sys
    syspath = os.path.join(CONF_TGTSYS_ROOT, 'sys')
    if not os.path.isdir(syspath):
        os.makedirs(syspath)
    if not os.path.exists(os.path.join(syspath, 'block')):
        #isys.mount('sysfs', 'sys', syspath)
        ret, msg = mount_dev('sysfs', 'sys', mntdir=syspath)
        
    if firstcall:
        _gen_fstab(mount_all_list)
        if CONF_USEUDEV:
            dolog('Copy device files to target system.')
            devdir = os.path.join(CONF_TGTSYS_ROOT, 'dev')
            if not os.path.isdir(devdir):
                os.makedirs(devdir)
            os.system('cp -a /dev/* %s' % devdir)
    if errmsg:
        return errmsg
    else:
        return  0

@register.server_handler('long')
def umount_all_tgtpart(mia, operid, mount_all_list, lastcall):
    # Umount proc.
    procdir = os.path.join(CONF_TGTSYS_ROOT, 'proc')
    ret,msg = umount_dev(procdir, rmdir=False)
    if not ret:
        dolog('Umount %s failed: %s\n' % (procdir, str(msg)))
    # Umount sys.
    sysdir = os.path.join(CONF_TGTSYS_ROOT, 'sys')
    ret, msg = umount_dev(sysdir, rmdir=False)
    if not ret:
        dolog('Umount %s failed: %s\n' % (sysdir, str(msg)))

    if os.path.exists('/tmpfs/debug/nomnttgt'):
        dolog('TURN ON: nomnttgt\n')
        return 0

    # Copy the installation log into the target system.
    if lastcall:
        logdir = os.path.join(CONF_TGTSYS_ROOT, 'var/log/MagicInstaller')
        os.system('mkdir -p %s' % logdir)
        os.system('cp /tmpfs/var/log/* %s' % logdir)
        os.system('cp /tmpfs/grub.* %s' % logdir)

    # Umount all filesystems and swapoff all swaps.
    cnt = 0
    mount_all_list.reverse()
    mia.set_step(operid, cnt, len(mount_all_list))
    for (mntpoint, devfn, fstype) in mount_all_list:
        if fstype == 'linux-swap':
            if lastcall:
                try:
                    isys.swapoff(devfn)
                except SystemError, em:
                    errmsg = _('swapoff(%s) failed: %s')
                    errmsg = errmsg % (devfn, str(em))
                    return  errmsg
        else:
            realpath = os.path.join(CONF_TGTSYS_ROOT, mntpoint[1:])
            ret, msg = umount_dev(realpath, rmdir=False)
            if not ret:
                errmsg = _('UMount %s failed: %s')
                errmsg = errmsg % (realpath, str(msg))
                return  errmsg
        cnt = cnt + 1
        mia.set_step(operid, cnt, len(mount_all_list))
    return  0
