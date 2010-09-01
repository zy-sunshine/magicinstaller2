#!/usr/bin/python
# Copyright (C) 2003, Charles Wang.
# Author:  Charles Wang <charles@linux.net.cn>
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANT; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public LIcense for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.

from gettext import gettext as _
import iconv
import sys
import kudzu
import parted

import isys

# Because the short operation and long operation are run in different process,
# they can't share the parted results. So all operations except status-free
# operation have to be 'long' even if it can terminate immediately.

if operation_type == 'short':
    # Status-free operations.

    def all_file_system_type():
        fstype_list = []
        fstype = parted.file_system_type_get_next()
        while fstype:
            if fstype_map.has_key(fstype.name):
                fstype_list.append(fstype.name)
            fstype = parted.file_system_type_get_next(fstype)
        return  fstype_list

    def all_disk_type():
        dtype_list = []
        dtype = parted.disk_type_get_next()
        while dtype:
            dtype_list.append(dtype.name)
            dtype = parted.disk_type_get_next(dtype)
        return  dtype_list

elif operation_type == 'long':
    # Status globals

    parted_MIN_FREESPACE = 2048  # 1M
    all_harddisks = {}

    # Status-Related operations.

    def device_probe_all(mia, operid, dummy):

        def get_device_list():
            result = []
            hd_list = kudzu.probe(kudzu.CLASS_HD,
                                  kudzu.BUS_IDE | kudzu.BUS_SCSI | kudzu.BUS_MISC,
                                  kudzu.PROBE_ALL)
            for hd in hd_list:
                try:
                    dev = parted.PedDevice.get(os.path.join('/dev/', hd.device))
                except:
                    pass
                else:
                    result.append(dev)
            return result

        global all_harddisks
        mia.set_step(operid, 0, -1)
        result = []
        # The following commented code is implemented by kudzu.
        devlist = get_device_list()
        if devlist:
            for dev in devlist:
                newdisklabel = None
                try:
                    disk = parted.PedDisk.new(dev)
                except parted.error:
                    # For the disk without any disk label, create it.
                    newdisklabel = 'y'
                    disk = dev.disk_new_fresh(parted.disk_type_get('msdos'))
                # Model might contain GB2312, it must be convert to Unicode.
                model = iconv.iconv('gb2312', 'utf8', dev.model).encode('utf8')
                result.append((dev.path, dev.length, model))
                all_harddisks[dev.path] = (dev, disk, newdisklabel)
        return  result

    def get_all_partitions(mia, operid, devpath):
        def part2result(part):
            flags = []
            avaflags = []
            label = 'N/A'
            if part.is_active() != 0:
                for f in range(parted.PARTITION_FIRST_FLAG,
                               parted.PARTITION_LAST_FLAG + 1):
                    if part.is_flag_available(f):
                        avaflags.append(f)
                        if part.get_flag(f):
                            flags.append(f)
                if part.disk.type.check_feature(parted.DISK_TYPE_PARTITION_NAME):
                    label = part.get_name()
            if part.fs_type:
                fs_type_name = part.fs_type.name
            else:
                fs_type_name = 'N/A'
            return (part.num, flags, part.type, part.geom.length,
                    fs_type_name, label, part.geom.start, part.geom.end, avaflags)

        result = []
        if all_harddisks.has_key(devpath):
            disk = all_harddisks[devpath][1]
            if disk:
                part = disk.next_partition()
                while part:
                    if part.type & parted.PARTITION_METADATA == 0:
                        result.append(part2result(part))
                    part = disk.next_partition(part)
        return  result

    def get_disk_type(mia, operid, devpath):
        if all_harddisks.has_key(devpath):
            disk = all_harddisks[devpath][1]
            if disk:
                if disk.type.check_feature(parted.DISK_TYPE_PARTITION_NAME):
                    support_partition_name = 'true'
                else:
                    support_partition_name = 'false'
                return (disk.type.name, support_partition_name)
        return  ('N/A', 'false')

    def _get_left_bound(sector, disk):
        under_sector = disk.get_partition_by_sector(sector)
        if not under_sector:
            return  sector
        if under_sector.type & parted.PARTITION_FREESPACE:
            return  under_sector.geom.start
        else:
            return  sector

    def _get_right_bound(sector, disk):
        under_sector = disk.get_partition_by_sector(sector)
        if not under_sector:
            return  sector
        if under_sector.type & parted.PARTITION_FREESPACE:
            return  under_sector.geom.end
        else:
            return  sector

    def _grow_over_small_freespace(geom, disk):
        if geom.length < parted_MIN_FREESPACE * 5:
            return  geom
        start = _get_left_bound(geom.start, disk)
        if start >= geom.end:
            return  None
        if geom.start - start < parted_MIN_FREESPACE:
            geom.set_start(start)
        end = _get_right_bound(geom.end, disk)
        if end <= geom.start:
            return  None
        if end - geom.end < parted_MIN_FREESPACE:
            geom.set_end(end)
        return  geom

    def add_partition(mia, operid, devpath, parttype, fstype, start, end):
        if all_harddisks.has_key(devpath):
            (dev, disk, dirty_or_not) = all_harddisks[devpath]
            if disk:
                constraint = dev.constraint_any()
                if parttype == 'primary':
                    parttype = 0
                elif parttype == 'extended':
                    parttype = parted.PARTITION_EXTENDED
                elif parttype == 'logical':
                    parttype = parted.PARTITION_LOGICAL
                if fstype != 'N/A':
                    fstype = parted.file_system_type_get(fstype)
                else:
                    fstype = None
                try:
                    newpart = disk.partition_new(parttype, fstype, start, end)
                    newgeom = _grow_over_small_freespace(newpart.geom, disk)
                    if newgeom:
                        newpart.geom.set_start(newgeom.start)
                        newpart.geom.set_end(newgeom.end)
                        disk.add_partition(newpart, constraint)
                        if fstype:
                            newpart.set_system(fstype)
                except  parted.error:
                    exc_info = sys.exc_info()
                    return (-1, str(exc_info[1]))
                all_harddisks[devpath] = (dev, disk, 'y')
                return (newpart.geom.start, '')
        return (-1, _("Can't find the specified disk."))

    def set_flags_and_label(mia, operid, devpath, part_start,
                            true_flags, false_flags, set_label, label):
        if all_harddisks.has_key(devpath):
            disk = all_harddisks[devpath][1]
            if disk:
                part = disk.next_partition()
                while part:
                    if part.geom.start == part_start:
                        for tf in true_flags:
                            part.set_flag(tf, 1)
                        for ff in false_flags:
                            part.set_flag(ff, 0)
                        if set_label == 'true':
                            part.set_name(label)
                        break
                    part = disk.next_partition(part)
                all_harddisks[devpath] = (all_harddisks[devpath][0], disk, 'y')
        return  0

    def delete_partition(mia, operid, devpath, part_start):
        if all_harddisks.has_key(devpath):
            disk  = all_harddisks[devpath][1]
            if disk:
                part = disk.next_partition()
                while part:
                    if part.geom.start == part_start:
                        disk.delete_partition(part)
                        break
                    part = disk.next_partition(part)
                all_harddisks[devpath] = (all_harddisks[devpath][0], disk, 'y')
        return get_all_partitions(mia, operid, devpath)

    def reload_partition_table(mia, operid, devpath):
        if all_harddisks.has_key(devpath):
            dev = all_harddisks[devpath][0]
            try:
                all_harddisks[devpath] = (dev, parted.PedDisk.new(dev), None)
            except parted.error:
                dltype = parted.disk_type_get('msdos')
                all_harddisks[devpath] = (dev, dev.disk_new_fresh(dltype), 'y')
        return 0

    def disk_new_fresh(mia, operid, devpath, dltype):
        dltype = parted.disk_type_get(dltype)
        if dltype and all_harddisks.has_key(devpath):
            dev = all_harddisks[devpath][0]
            all_harddisks[devpath] = (dev, dev.disk_new_fresh(dltype), 'y')
        return 0

    def get_all_dirty_disk(mia, operid, dummy):
        mia.set_step(operid, 0, -1)
        result = []
        for devpath in all_harddisks.keys():
            if all_harddisks[devpath][2]:
                result.append(devpath)
        return  result

    def commit_devpath(mia, operid, devpath):
        mia.set_step(operid, 0, -1)
        if all_harddisks.has_key(devpath):
            disk  = all_harddisks[devpath][1]
            if disk:
                try:
                    disk.commit()
                    all_harddisks[devpath] = (all_harddisks[devpath][0], disk, None)
                except parted.error, errmsg:
                    return  str(errmsg)
        return  0

    def format_partition(mia, operid, devpath, part_start, fstype):
        mia.set_step(operid, 0, -1)
        if not fstype_map.has_key(fstype):
            errmsg = _('Unrecoginzed filesystem %s.')
            return errmsg % fstype
        if fstype_map[fstype][1] == '':
            errmsg = _('Format %s is not supported.')
            return errmsg % fstype
        if not all_harddisks.has_key(devpath):
            return _('No such device: ') + devpath
        disk = all_harddisks[devpath][1]
        if not disk:
            return _('Not any partition table found on: ') + devpath
        part = disk.next_partition()
        while part:
            if part.geom.start != part_start:
                part = disk.next_partition(part)
                continue
            if fstype_map[fstype][1] == 'internal':
                parted_fstype = parted.file_system_type_get(fstype)
                try:
                    fs = part.geom.file_system_create(parted_fstype)
                    del(fs)
                    part.set_system(parted_fstype)
                    disk.commit()
                    return  0
                except parted.error, errmsg:
                    return  str(errmsg)
            else:
                parted_fstype = parted.file_system_type_get(fstype)
                try:
                    part.set_system(parted_fstype)
                    disk.commit()
                except parted.error, errmsg:
                    return  str(errmsg)
                time.sleep(1)
                cmd = '%s %s%d' % (fstype_map[fstype][1], devpath, part.num)
                r = os.system(cmd)
                if r != 0:
                    errmsg = _('Run "%s" failed.')
                    return  errmsg % cmd
                else:
                    return  0
        return _('Not any partition found on position: ') + str(part_start)

    def _gen_fstab(mount_all_list):
        global  tgtsys_root
        # Generate fstab.
        mountmap = {}
        for (mntdir, devfn, fstype) in mount_all_list:
            if fstype == 'linux-swap':  continue
            if fstype in ('fat32', 'fat16'):
                mountmap[mntdir] = (devfn, fstype_map[fstype][0],
                                    'iocharset=cp936,umask=0,defaults', 0, 0)
            elif mntdir == '/':
                mountmap[mntdir] = (devfn, fstype_map[fstype][0],
                                    'defaults', 1, 1)
            else:
                mountmap[mntdir] = (devfn, fstype_map[fstype][0],
                                    'defaults', 0, 0)
        mountmap['/dev/pts'] = ('none', 'devpts', 'gid=5,mode=620', 0, 0)
        mountmap['/proc']    = ('none', 'proc', 'defaults', 0, 0)
        mountmap['/sys']     = ('none', 'sysfs', 'defaults', 0, 0)
        mountmap['/dev/shm'] = ('none', 'tmpfs', 'defaults', 0, 0)
        #
        fdlist = kudzu.probe(kudzu.CLASS_FLOPPY,
                             kudzu.BUS_IDE | kudzu.BUS_SCSI | kudzu.BUS_MISC,
                             kudzu.PROBE_ALL)
        cdlist = kudzu.probe(kudzu.CLASS_CDROM,
                             kudzu.BUS_IDE | kudzu.BUS_SCSI | kudzu.BUS_MISC,
                             kudzu.PROBE_ALL)
        for fd in fdlist:
            mntdir = string.replace(fd.device, 'fd', '/media/floppy')
            if mntdir == '/media/floppy0':  mntdir = '/media/floppy'
            mountmap[mntdir] = (os.path.join('/dev', fd.device),
                                'auto', 'iocharset=cp936,noauto,user,kudzu,rw,exec,sync', 0, 0)
            os.system('mkdir -p %s' % os.path.join(tgtsys_root, mntdir[1:]))
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
                                    'iso9660,udf', 'iocharset=cp936,noauto,user,kudzu,ro,exec', 0, 0)
                devdir = os.path.join(tgtsys_root, 'dev')
                os.system('mkdir -p %s' % devdir)
                os.system('ln -s %s %s' % \
                          (cddevlist[cnt],
                           os.path.join(devdir,
                                        os.path.basename(mntdir))))
                os.system('mkdir -p %s' % os.path.join(tgtsys_root, mntdir[1:]))
                cnt = cnt + 1
        etcpath = os.path.join(tgtsys_root, 'etc')
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

    def mount_all_tgtpart(mia, operid, mount_all_list, firstcall):
        global useudev

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
                            return  str(em)
                else:
                    realpath = os.path.join(tgtsys_root, mntpoint[1:])
                    if not os.path.isdir(realpath):
                        try:
                            os.makedirs(os.path.join(tgtsys_root, mntpoint[1:]))
                        except OSError, em:
                            errmsg = _('Can not make directory %s: %s')
                            errmsg = errmsg % (realpath, str(em))
                            return  errmsg
                    try:
                        isys.mount(fstype_map[fstype][0], devfn, realpath, 0, 0)
                    except SystemError, em:
                        errmsg = _('Mount %s on %s as %s failed: %s')
                        errmsg = errmsg % (devfn, realpath, fstype, str(em))
                        return  errmsg
                cnt = cnt + 1
                mia.set_step(operid, cnt, len(mount_all_list))
        # Mount /proc.
        procpath = os.path.join(tgtsys_root, 'proc')
        if not os.path.isdir(procpath):
            os.makedirs(procpath)
        if not os.path.exists(os.path.join(procpath, 'cmdline')):
            isys.mount('proc', 'proc', procpath, 0, 0)
        # Mount /sys
        syspath = os.path.join(tgtsys_root, 'sys')
        if not os.path.isdir(syspath):
            os.makedirs(syspath)
        if not os.path.exists(os.path.join(syspath, 'block')):
            isys.mount('sysfs', 'sys', syspath, 0, 0)
            
        if firstcall:
            _gen_fstab(mount_all_list)
            if useudev:
                dolog('Copy device files to target system.')
                devdir = os.path.join(tgtsys_root, 'dev')
                if not os.path.isdir(devdir):
                    os.makedirs(devdir)
                os.system('cp -a /dev/* %s' % devdir)

        return  0

    def umount_all_tgtpart(mia, operid, mount_all_list, lastcall):
        # Umount proc.
        procdir = os.path.join(tgtsys_root, 'proc')
        try:
            isys.umount(procdir)
        except Exception, errmsg:
            dolog('Umount %s failed: %s\n' % (procdir, str(errmsg)))
        # Umount sys.
        sysdir = os.path.join(tgtsys_root, 'sys')
        try:
            isys.umount(sysdir)
        except Exception, errmsg:
            dolog('Umount %s failed: %s\n' % (sysdir, str(errmsg)))

        if os.path.exists('/tmpfs/debug/nomnttgt'):
            dolog('TURN ON: nomnttgt\n')
            return 0

        # Copy the installation log into the target system.
        if lastcall:
            logdir = os.path.join(tgtsys_root, 'var/log/MagicInstaller')
            os.system('mkdir -p %s' % logdir)
            os.system('cp /tmpfs/var/log/* %s' % logdir)
            os.system('cp /tmpfs/grub.* %s' % logdir)
            #os.system('cp %s/* %s' % (MBRoot, logdir))

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
                realpath = os.path.join(tgtsys_root, mntpoint[1:])
                try:
                    isys.umount(realpath)
                except SystemError, em:
                    errmsg = _('UMount %s failed: %s')
                    errmsg = errmsg % (realpath, str(em))
                    return  errmsg
            cnt = cnt + 1
            mia.set_step(operid, cnt, len(mount_all_list))
        return  0
