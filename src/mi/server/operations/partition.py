#!/usr/bin/python
#encoding=utf8

from mi.client.utils import _
import sys, os, time, string
import parted, _ped #@UnresolvedImport
from mi.utils.common import mount_dev, umount_dev, run_bash
# Because the short operation and long operation are run in different process,
# they can't share the parted results. So all operations except status-free
# operation have to be 'long' even if it can terminate immediately.

from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()

from mi.utils.miregister import MiRegister
register = MiRegister()

from mi.server.utils import logger
dolog = logger.info

# Status-free operations.
@register.server_handler('short')
def all_file_system_type():
    fs_map = parted.fileSystemType
    fs_list = fs_map.keys()
    if 'linux-swap' not in fs_list:
        fs_list.append('linux-swap')
    return  fs_list

@register.server_handler('short')
def all_disk_type():
    dtype_map = parted.diskType
    dtype_list = dtype_map.keys()
    return  dtype_list
    
#-------------------- long operations ---------------------------
# Status globals

parted_MIN_FREESPACE = 2048  # 1M

# Status-Related operations.

@register.server_handler('long')
def revision_fstype(fstype):
    ''' revise the file system version between MI and to libparted, current only linux-swap version '''
    if fstype == 'linux-swap':
        fstype = 'linux-swap(v1)'
    return fstype
    
@register.server_handler('long')
def device_probe_all(mia, operid, dummy):
    def get_device_list():
        hd_list = filter(lambda d: d.type != parted.DEVICE_DM and \
                         d.readOnly != True, # CD-ROM will be read only. 
                         parted.getAllDevices())
        
        return hd_list

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
            model = str(dev.model)
            try:
                model = model.decode('gb18030').encode('utf8')
            except UnicodeDecodeError, e:
                pass

            result.append((dev.path, dev.length, model))
            CF.S.all_harddisks[dev.path] = (dev, disk, newdisklabel)
    dolog('operations.parted.device_probe_all: %s\n' % str(result))
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
        
        return (part.number, flags, part.type, part.geometry.length,
                fs_type_name, label, part.geometry.start, part.geometry.end, avaflags)

    result = []
    if CF.S.all_harddisks.has_key(devpath):
        disk = CF.S.all_harddisks[devpath][1]
        if disk:
            try:
                part = disk.getFirstPartition()
            except:
                logger.warn('devpath %s can not get one partition.' % devpath)
            else:
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
    dolog('operations.parted.get_all_partitions: %s\n' % str(result))
    return  result

@register.server_handler('long')
def get_disk_type(mia, operid, devpath):
    if CF.S.all_harddisks.has_key(devpath):
        disk = CF.S.all_harddisks[devpath][1]
        if disk:
            if disk.supportsFeature(parted.DISK_TYPE_PARTITION_NAME):
                support_partition_name = 'true'
            else:
                support_partition_name = 'false'
            return (disk.type, support_partition_name)
    return  ('N/A', 'false')

def _get_left_bound(sector, disk):
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
    logger.d('add_partition %s' % str((devpath, parttype, fstype, start, end)))
    fstype = revision_fstype(fstype)
    if CF.S.all_harddisks.has_key(devpath):
        (dev, disk, dirty_or_not) = CF.S.all_harddisks[devpath]
        if disk:
            constraint = parted.Constraint(device=dev)#exactGeom=newgeom)
            if parttype == 'primary':
                parttype = 0
            elif parttype == 'extended':
                parttype = parted.PARTITION_EXTENDED
            elif parttype == 'logical':
                parttype = parted.PARTITION_LOGICAL
            if fstype != 'N/A':
                fstype = parted.fileSystemType[fstype]
            else:
                fstype = None
            try:
                newgeom_bound = _grow_over_small_freespace(start, end, disk)
                if not newgeom_bound:
                    return (-1, "Can't get the geometry of new partition (start=%s end=%s)." % (start, end))
                newgeom = parted.Geometry(device=dev, start=newgeom_bound[0], end=newgeom_bound[1])
                # We can use _ped's geometry to build parted's Geometry
                if newgeom:
                    newpart = parted.Partition(disk=disk, type=parttype, geometry=newgeom)
                    disk.addPartition(partition=newpart, constraint=constraint)
                    if fstype:
                        newpart.getPedPartition().set_system(fstype)
            except _ped.PartitionException, errmsg:
                return(-1, str(errmsg))
            CF.S.all_harddisks[devpath] = (dev, disk, 'y')
            return (newpart.geometry.start, '')
    return (-1, _("Can't find the specified disk."))

@register.server_handler('long')
def set_flags_and_label(mia, operid, devpath, part_start,
                        true_flags, false_flags, set_label, label):
    logger.d('set_flags_and_label %s', str((devpath, part_start,
                        true_flags, false_flags, set_label, label)))
    if CF.S.all_harddisks.has_key(devpath):
        disk = CF.S.all_harddisks[devpath][1]
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

            CF.S.all_harddisks[devpath] = (CF.S.all_harddisks[devpath][0], disk, 'y')
    return  0

@register.server_handler('long')
def delete_partition(mia, operid, devpath, part_start):
    logger.d('delete_partition %s' % str((devpath, part_start)))
    if CF.S.all_harddisks.has_key(devpath):
        disk  = CF.S.all_harddisks[devpath][1]
        if disk:
            part = disk.getFirstPartition()
            while part:
                if part.geometry.start == part_start:
                    disk.removePartition(part)
                    break
                part = part.nextPartition()
            CF.S.all_harddisks[devpath] = (CF.S.all_harddisks[devpath][0], disk, 'y')
    return get_all_partitions(mia, operid, devpath)

@register.server_handler('long')
def reload_partition_table(mia, operid, devpath):
    logger.d('reload_partition_table %s' % devpath)
    if CF.S.all_harddisks.has_key(devpath):
        dev = CF.S.all_harddisks[devpath][0]
        try:
            CF.S.all_harddisks[devpath] = (dev, parted.Disk(dev), None)
        except _ped.DiskLabelException:
            dltype = parted.diskType['msdos']
            CF.S.all_harddisks[devpath] = (dev, parted.freshDisk(device=dev, ty=dltype), 'y')
    return 0

@register.server_handler('long')
def disk_new_fresh(mia, operid, devpath, dltype):
    logger.d('disk_new_fresh %s %s' % (devpath, dltype))
    #dltype = parted.disk_type_get(dltype)
    dltype = parted.diskType[dltype]
    if dltype and CF.S.all_harddisks.has_key(devpath):
        dev = CF.S.all_harddisks[devpath][0]
        #CF.S.all_harddisks[devpath] = (dev, dev.disk_new_fresh(dltype), 'y')
        CF.S.all_harddisks[devpath] = (dev, parted.freshDisk(device=dev, ty=dltype), 'y')
    return 0

@register.server_handler('long')
def get_all_dirty_disk(mia, operid, dummy):
    mia.set_step(operid, 0, -1)
    result = []
    for devpath in CF.S.all_harddisks.keys():
        if CF.S.all_harddisks[devpath][2]:
            result.append(devpath)
    logger.d('get_all_dirty_disk result: %s' % str(result))
    return result

@register.server_handler('long')
def commit_devpath(mia, operid, devpath):
    logger.d('commit_devpath %s' % devpath)
    mia.set_step(operid, 0, -1)
    if CF.S.all_harddisks.has_key(devpath):
        disk  = CF.S.all_harddisks[devpath][1]
        if disk:
            try:
                disk.commit()
                CF.S.all_harddisks[devpath] = (CF.S.all_harddisks[devpath][0], disk, None)
            #except parted.error, errmsg:
            except parted.DiskException as errmsg:
                return  str(errmsg)
    return  0

@register.server_handler('long')
def format_partition(mia, operid, devpath, part_start, fstype):
    logger.d('format_partition device: %s partition start: %s fstype: %s' % (devpath, part_start, fstype))
    mia.set_step(operid, 0, -1)
    if not CF.D.FSTYPE_MAP.has_key(fstype):
        errmsg = _('Unrecoginzed filesystem %s.')
        return errmsg % fstype
    if CF.D.FSTYPE_MAP[fstype][1] == '':
        errmsg = _('Format %s is not supported.')
        return errmsg % fstype
    if not CF.S.all_harddisks.has_key(devpath):
        return _('No such device: ') + devpath
    disk = CF.S.all_harddisks[devpath][1]
    if not disk:
        return _('Not any partition table found on: ') + devpath

    part = disk.getFirstPartition()
    while part:
        if part.geometry.start != part_start:
            part = part.nextPartition()
            continue
        if CF.D.FSTYPE_MAP[fstype][1] == 'internal':
            parted_fstype = parted.fileSystemType[revision_fstype(fstype)]
            try:
                part.getPedPartition().set_system(parted_fstype)
                logger.d('Create internal fstype %s on device %s partition start %s' % (fstype, devpath, part_start))
                part.fileSystem.create()
                disk.commit()
                logger.d('Create internal partition complete!')
            except NotImplementedError, errmsg:
                return  str(errmsg)
            except parted.DiskException as errmsg:
                return  str(errmsg)
            return  0
        else:
            parted_fstype = parted.fileSystemType[revision_fstype(fstype)]
            try:
                part.getPedPartition().set_system(parted_fstype)
                disk.commit()
            except NotImplementedError, errmsg:
                return  str(errmsg)
            except parted.DiskException as errmsg:
                return  str(errmsg)
            
            def try_format(devn, id_):
                # Wait for device block appear.
                fblk = False
                time.sleep(1)
                # We attemp to detect device file whether exists
                for trycnt in range(10):
                    # os.path.exists cannot detect file exists real time
                    #if os.path.exists(devn):
                    if os.system('ls %s' % devn) == 0:
                        fblk = True
                        break
                    else:
                        time.sleep(1)
                        
                if not fblk:
                    msg = _('Not exists device block on %s: \ntry time: %d\n') % (devpath, trycnt)
                    logger.w(msg)
                    return msg
                else:
                    logger.d('try_format %s ls device %s time' % (id_, trycnt))
                # Run command to format partition
                cmd_format = CF.D.FSTYPE_MAP[fstype][1]
                cmd_f_list = cmd_format.split()
                cmd = cmd_f_list[0]
                argv = cmd_f_list[1:]
                argv.append(devn)
                cmdres = run_bash(cmd, argv)
                logger.d('%s %s' % (cmd, ' '.join(argv)))
                logger.d(' '.join(cmdres['out']))
                if cmdres['ret'] != 0:
                    errmsg = _('Run "%s %s" failed: %s\ntry time: %d\n')
                    return  errmsg % ( cmd, ' '.join(argv), str(cmdres['err']), trycnt )
                else:
                    return  0
                
            ret = 'None'
            for t in range(5):
                ret = try_format('%s%d' % (devpath, part.number), t)
                if ret == 0:
                    break
            else:
                logger.d('try format time %s time, but can not format at last!' % t)
                
            return ret
        
    return _('Not any partition found on position: ') + str(part_start)
